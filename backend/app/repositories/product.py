from typing import Optional

import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_
from app.models.models import Product
from app.repositories.base import BaseProductRepo
from app.schemas.repo import ProductOut


def _to_product_out(product: Product) -> ProductOut:
    return ProductOut(
        id=str(product.id),
        name=product.name,
        category=product.category or "",
        return_window_days=product.return_window_days or 0,
        warranty_months=product.warranty_months or 0,
    )


class ProductRepo(BaseProductRepo):
    def __init__(self, db: Session):
        super().__init__(db)

    def get_by_external_id(self, product_id: str) -> Optional[ProductOut]:
        logger = AppLoggerAdapter(
            logging.getLogger(__name__),
            {
                "layer": LogLayer.DB,
                "category": LogCategory.DATABASE,
                "component": __name__,
            },
        )
        try:
            product = self.db.scalar(
                select(Product).where(Product.external_product_id == product_id)
            )
            if product is None:
                logger.debug(
                    "Product not found",
                    extra=extra_(
                        operation="repo_get_product",
                        status="skipped",
                        product_id=product_id,
                    ),
                )
                return None
            return _to_product_out(product)
        except Exception:
            logger.exception(
                "Failed to fetch product",
                extra=extra_(
                    operation="repo_get_product",
                    status="failure",
                    product_id=product_id,
                ),
            )
            raise
