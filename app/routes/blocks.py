from flask import Blueprint, jsonify, request

from app.auth import require_role
from app.errors import BadRequestError
from app.services.block_service import BlockService

blocks_bp = Blueprint("blocks", __name__)


@blocks_bp.post("")
@require_role("ADMIN", "MANAGER")
def create_block():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    block = BlockService.create_block(payload)
    return jsonify(block.to_dict()), 201


@blocks_bp.get("/<int:block_id>")
@require_role("ADMIN", "MANAGER", "GUEST")
def get_block(block_id: int):
    block = BlockService.get_block(block_id)
    return jsonify(block.to_dict()), 200


@blocks_bp.get("")
@require_role("ADMIN", "MANAGER", "GUEST")
def list_blocks():
    prop_id_raw = request.args.get("property_id")
    prop_id = None
    if prop_id_raw is not None:
        if not prop_id_raw.isdigit():
            raise BadRequestError("property_id query parameter must be an integer.")
        prop_id = int(prop_id_raw)
    blocks = BlockService.list_blocks(property_id=prop_id)
    return jsonify([b.to_dict() for b in blocks]), 200


@blocks_bp.route("/<int:block_id>", methods=["PUT", "PATCH"])
@require_role("ADMIN", "MANAGER")
def update_block(block_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a valid JSON object.")
    block = BlockService.update_block(block_id, payload)
    return jsonify(block.to_dict()), 200


@blocks_bp.delete("/<int:block_id>")
@require_role("ADMIN", "MANAGER")
def delete_block(block_id: int):
    BlockService.delete_block(block_id)
    return "", 204
