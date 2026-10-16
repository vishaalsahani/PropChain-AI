// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract DocumentRegistry {
    struct Record {
        bytes32 fileHash;
        uint256 timestamp;
        address uploader;
        bool exists;
    }

    mapping(uint256 => Record) public records;
    uint256 public recordCount;

    event DocumentRegistered(uint256 indexed documentId, bytes32 fileHash, address indexed uploader, uint256 timestamp);

    function registerDocument(uint256 documentId, bytes32 fileHash) external {
        require(!records[documentId].exists, "Already registered");
        records[documentId] = Record({
            fileHash: fileHash,
            timestamp: block.timestamp,
            uploader: msg.sender,
            exists: true
        });
        recordCount += 1;
        emit DocumentRegistered(documentId, fileHash, msg.sender, block.timestamp);
    }

    function verifyDocument(uint256 documentId, bytes32 fileHash) external view returns (bool) {
        Record memory record = records[documentId];
        require(record.exists, "Not registered");
        return record.fileHash == fileHash;
    }
}
