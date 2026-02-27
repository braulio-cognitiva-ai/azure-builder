"""Pricing Service - Azure Retail Prices API integration."""
import httpx
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models import PricingCache


class PricingService:
    """Service for Azure pricing data."""
    
    def __init__(self, session: AsyncSession):
        """Initialize pricing service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.api_url = settings.azure_pricing_api_url
        self.cache_ttl = settings.pricing_cache_ttl
    
    async def get_price(
        self,
        service: str,
        sku: str,
        region: str
    ) -> Optional[Decimal]:
        """Get price for a specific service/SKU/region.
        
        Args:
            service: Azure service name (e.g., "Virtual Machines")
            sku: SKU name (e.g., "P1V2")
            region: Azure region (e.g., "eastus")
        
        Returns:
            Unit price (per hour) or None if not found
        """
        # Check cache first
        cached_price = await self._get_cached_price(service, sku, region)
        if cached_price:
            return cached_price
        
        # Query Azure Retail Prices API
        try:
            price = await self._query_azure_pricing_api(service, sku, region)
            
            if price:
                # Cache the result
                await self._cache_price(service, sku, region, price)
            
            return price
        except Exception as e:
            # Log error but don't fail - return None
            print(f"Error querying Azure pricing API: {e}")
            return None
    
    async def estimate_monthly_cost(self, resources: list[dict]) -> dict:
        """Estimate total monthly cost for a list of resources.
        
        Args:
            resources: List of resource definitions with type, sku, region
        
        Returns:
            Dict with total cost and breakdown
        """
        breakdown = []
        total = Decimal("0.00")
        
        for resource in resources:
            price = await self.get_price(
                service=resource.get("type", ""),
                sku=resource.get("sku", ""),
                region=resource.get("region", "eastus")
            )
            
            if price:
                # Assume 730 hours/month
                monthly = price * 730
                breakdown.append({
                    "resource": resource.get("name", "Unknown"),
                    "service": resource.get("type", ""),
                    "sku": resource.get("sku", ""),
                    "region": resource.get("region", ""),
                    "monthly_cost": float(monthly)
                })
                total += monthly
            else:
                breakdown.append({
                    "resource": resource.get("name", "Unknown"),
                    "service": resource.get("type", ""),
                    "sku": resource.get("sku", ""),
                    "region": resource.get("region", ""),
                    "monthly_cost": 0.0,
                    "note": "Pricing not available"
                })
        
        return {
            "total_monthly": float(total),
            "currency": "USD",
            "breakdown": breakdown
        }
    
    async def compare_regions(
        self,
        resources: list[dict],
        regions: list[str]
    ) -> dict:
        """Compare cost across multiple regions.
        
        Args:
            resources: List of resource definitions
            regions: List of regions to compare
        
        Returns:
            Dict with cost per region
        """
        comparison = {}
        
        for region in regions:
            # Clone resources with new region
            regional_resources = [
                {**r, "region": region} for r in resources
            ]
            
            estimate = await self.estimate_monthly_cost(regional_resources)
            comparison[region] = estimate["total_monthly"]
        
        return {
            "regions": comparison,
            "cheapest": min(comparison, key=comparison.get),
            "most_expensive": max(comparison, key=comparison.get)
        }
    
    async def compare_skus(
        self,
        service: str,
        skus: list[str],
        region: str
    ) -> dict:
        """Compare cost across multiple SKUs for a service.
        
        Args:
            service: Azure service name
            skus: List of SKU names
            region: Azure region
        
        Returns:
            Dict with cost per SKU
        """
        comparison = {}
        
        for sku in skus:
            price = await self.get_price(service, sku, region)
            if price:
                comparison[sku] = {
                    "hourly": float(price),
                    "monthly": float(price * 730)
                }
            else:
                comparison[sku] = {
                    "hourly": None,
                    "monthly": None,
                    "note": "Pricing not available"
                }
        
        return comparison
    
    async def _get_cached_price(
        self,
        service: str,
        sku: str,
        region: str
    ) -> Optional[Decimal]:
        """Get price from cache if not expired.
        
        Args:
            service: Service name
            sku: SKU name
            region: Region
        
        Returns:
            Cached price or None
        """
        cutoff = datetime.utcnow() - timedelta(seconds=self.cache_ttl)
        
        stmt = select(PricingCache).where(
            PricingCache.service == service,
            PricingCache.sku == sku,
            PricingCache.region == region,
            PricingCache.last_updated >= cutoff
        )
        
        result = await self.session.execute(stmt)
        cached = result.scalar_one_or_none()
        
        return cached.price if cached else None
    
    async def _cache_price(
        self,
        service: str,
        sku: str,
        region: str,
        price: Decimal,
        raw_data: Optional[dict] = None
    ):
        """Cache pricing data.
        
        Args:
            service: Service name
            sku: SKU name
            region: Region
            price: Unit price
            raw_data: Full API response data
        """
        # Check if already exists
        stmt = select(PricingCache).where(
            PricingCache.service == service,
            PricingCache.sku == sku,
            PricingCache.region == region
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing
            existing.price = price
            existing.last_updated = datetime.utcnow()
            existing.raw_data = raw_data or {}
        else:
            # Create new
            cache_entry = PricingCache(
                service=service,
                sku=sku,
                region=region,
                meter=sku,  # Using SKU as meter for simplicity
                price=price,
                currency="USD",
                unit_of_measure="1 Hour",
                raw_data=raw_data or {},
                last_updated=datetime.utcnow()
            )
            self.session.add(cache_entry)
        
        await self.session.commit()
    
    async def _query_azure_pricing_api(
        self,
        service: str,
        sku: str,
        region: str
    ) -> Optional[Decimal]:
        """Query Azure Retail Prices API.
        
        Args:
            service: Service name
            sku: SKU name
            region: Region
        
        Returns:
            Unit price or None
        """
        # Build filter query
        # API docs: https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices
        
        # Map region names (e.g., eastus → East US)
        region_map = {
            "eastus": "East US",
            "westus": "West US",
            "westus2": "West US 2",
            "centralus": "Central US",
            "northeurope": "North Europe",
            "westeurope": "West Europe",
            "southeastasia": "Southeast Asia",
            "eastasia": "East Asia",
        }
        
        azure_region = region_map.get(region.lower(), region)
        
        # Build filter string
        filter_parts = []
        filter_parts.append(f"armRegionName eq '{azure_region}'")
        
        # Map service names to API service names
        service_map = {
            "App Service": "Azure App Service",
            "App Service Plan": "Azure App Service",
            "SQL Database": "SQL Database",
            "SQL Server": "SQL Database",
            "Storage Account": "Storage",
            "Virtual Machine": "Virtual Machines",
            "Container Apps": "Container Apps",
            "CosmosDB": "Azure Cosmos DB",
            "Functions": "Azure Functions",
        }
        
        api_service_name = service_map.get(service, service)
        filter_parts.append(f"serviceName eq '{api_service_name}'")
        
        # Add SKU filter if applicable
        if sku:
            filter_parts.append(f"armSkuName eq '{sku}'")
        
        filter_query = " and ".join(filter_parts)
        
        # Query API with pagination
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                params = {
                    "$filter": filter_query,
                    "currencyCode": "USD",
                    "top": 100
                }
                
                response = await client.get(
                    self.api_url,
                    params=params
                )
                response.raise_for_status()
                
                data = response.json()
                items = data.get("Items", [])
                
                if items:
                    # Get first matching item
                    item = items[0]
                    unit_price = item.get("retailPrice", 0.0)
                    
                    # Cache raw data
                    await self._cache_price(
                        service,
                        sku,
                        region,
                        Decimal(str(unit_price)),
                        raw_data=item
                    )
                    
                    return Decimal(str(unit_price))
                else:
                    # No results - try fallback with looser filter
                    return await self._fallback_pricing(service, sku, region)
                
            except Exception as e:
                print(f"Azure Pricing API error: {e}")
                return await self._fallback_pricing(service, sku, region)
    
    async def _fallback_pricing(
        self,
        service: str,
        sku: str,
        region: str
    ) -> Optional[Decimal]:
        """Fallback pricing estimates when API fails.
        
        Uses rough estimates based on typical Azure pricing.
        """
        # Rough estimates for common services (per hour)
        estimates = {
            ("App Service", "B1"): "0.075",
            ("App Service", "P1V2"): "0.198",
            ("App Service", "P2V2"): "0.396",
            ("SQL Database", "Basic"): "0.0068",
            ("SQL Database", "S1"): "0.0203",
            ("SQL Database", "P1"): "0.1697",
            ("Storage Account", "Standard_LRS"): "0.002",
            ("Virtual Machine", "Standard_B2s"): "0.041",
            ("Container Apps", "Consumption"): "0.000016",
            ("CosmosDB", "Standard"): "0.008",
        }
        
        key = (service, sku)
        if key in estimates:
            return Decimal(estimates[key])
        
        return None
