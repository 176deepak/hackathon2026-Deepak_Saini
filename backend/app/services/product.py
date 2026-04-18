from typing import Optional

import logging
from app.repositories.base import BaseProductRepo
from app.schemas.repo import ProductOut
from app.services.base import BaseService
from app.core.logging import AppLoggerAdapter, LogCategory, LogLayer, extra_

logger = AppLoggerAdapter(
    logging.getLogger(__name__),
    {
        "layer": LogLayer.SERVICE,
        "category": LogCategory.API,
        "component": __name__,
    },
)


class ProductService(BaseService):
    def __init__(self, product_repo: BaseProductRepo):
        super().__init__(product_repo=product_repo)

    def get_product(self, product_id: str) -> Optional[ProductOut]:
        normalized_product_id = self._safe_str(product_id)
        self._validate_non_empty(normalized_product_id, "product_id")
        try:
            product = self.product_repo.get_by_external_id(normalized_product_id)
            logger.debug(
                "Product fetched",
                extra=extra_(
                    operation="svc_get_product",
                    status="success" if product else "skipped",
                    product_id=normalized_product_id,
                ),
            )
            return product
        except Exception:
            logger.exception(
                "Failed to fetch product",
                extra=extra_(
                    operation="svc_get_product",
                    status="failure",
                    product_id=normalized_product_id,
                ),
            )
            raise
