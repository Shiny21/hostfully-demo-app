from sqlalchemy import select

from app.errors import BadRequestError, NotFoundError
from app.extensions import db
from app.models import Block
from app.repositories.availability import AvailabilityRepository
from app.schemas import BlockCreateSchema, BlockUpdateSchema


class BlockService:
    @staticmethod
    def create_block(payload: dict) -> Block:
        data = BlockCreateSchema.model_validate(payload)
        AvailabilityRepository.lock_and_get_property(data.property_id)
        AvailabilityRepository.assert_no_overlap(
            property_id=data.property_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        block = Block(
            property_id=data.property_id,
            start_date=data.start_date,
            end_date=data.end_date,
        )
        db.session.add(block)
        db.session.commit()
        return block

    @staticmethod
    def get_block(block_id: int) -> Block:
        block = db.session.get(Block, block_id)
        if not block:
            raise NotFoundError(f"Block with id {block_id} was not found.")
        return block

    @staticmethod
    def list_blocks(property_id: int | None = None) -> list[Block]:
        stmt = select(Block).order_by(Block.start_date.asc(), Block.id.asc())
        if property_id is not None:
            stmt = stmt.where(Block.property_id == property_id)
        return list(db.session.execute(stmt).scalars().all())

    @staticmethod
    def update_block(block_id: int, payload: dict) -> Block:
        if not payload:
            raise BadRequestError("Update payload cannot be empty.")
        data = BlockUpdateSchema.model_validate(payload)
        block = BlockService.get_block(block_id)
        AvailabilityRepository.lock_and_get_property(block.property_id)

        new_start = data.start_date if data.start_date is not None else block.start_date
        new_end = data.end_date if data.end_date is not None else block.end_date
        if new_start >= new_end:
            raise BadRequestError("start_date must be strictly before end_date")

        AvailabilityRepository.assert_no_overlap(
            property_id=block.property_id,
            start_date=new_start,
            end_date=new_end,
            exclude_block_id=block.id,
        )
        block.start_date = new_start
        block.end_date = new_end
        db.session.commit()
        return block

    @staticmethod
    def delete_block(block_id: int) -> None:
        block = BlockService.get_block(block_id)
        db.session.delete(block)
        db.session.commit()
