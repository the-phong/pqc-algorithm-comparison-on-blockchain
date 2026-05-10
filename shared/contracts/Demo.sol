// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Demo {
    struct Record {
        uint256 recordId;
        address owner;
        bytes payload;
        bytes32 payloadHash;
        bytes32 pqcProofHash;
        uint256 appNonce;
        uint256 timestamp;
        bool encrypted;
        string mode;
        string ipfsCid;
        string algorithm;
    }

    uint256 public lastRecordId;
    mapping(uint256 => Record) private records;

    mapping(address => uint256) public lastNonceBySender;

    event RecordStored(
        uint256 indexed recordId,
        address indexed owner,
        bytes payload,
        bytes32 payloadHash,
        bytes32 pqcProofHash,
        uint256 appNonce,
        uint256 timestamp,
        bool encrypted,
        string mode,
        string ipfsCid,
        string algorithm
    );

    function storeRecord(
        bytes memory payload,
        bytes32 payloadHash,
        bytes32 pqcProofHash,
        uint256 appNonce,
        uint256 timestamp,
        bool encrypted,
        string memory mode,
        string memory ipfsCid,
        string memory algorithm
    ) public {
        require(appNonce > lastNonceBySender[msg.sender], "stale nonce");
        require(keccak256(payload) == payloadHash, "payload hash mismatch");

        uint256 recordId = lastRecordId + 1;
        lastRecordId = recordId;

        records[recordId] = Record({
            recordId: recordId,
            owner: msg.sender,
            payload: payload,
            payloadHash: payloadHash,
            pqcProofHash: pqcProofHash,
            appNonce: appNonce,
            timestamp: timestamp,
            encrypted: encrypted,
            mode: mode,
            ipfsCid: ipfsCid,
            algorithm: algorithm
        });

        lastNonceBySender[msg.sender] = appNonce;

        emit RecordStored(
            recordId,
            msg.sender,
            payload,
            payloadHash,
            pqcProofHash,
            appNonce,
            timestamp,
            encrypted,
            mode,
            ipfsCid,
            algorithm
        );
    }

    function getRecord(
        uint256 recordId
    )
        public
        view
        returns (
            uint256,
            address,
            bytes memory,
            bytes32,
            bytes32,
            uint256,
            uint256,
            bool,
            string memory,
            string memory,
            string memory
        )
    {
        Record storage record = records[recordId];
        return (
            record.recordId,
            record.owner,
            record.payload,
            record.payloadHash,
            record.pqcProofHash,
            record.appNonce,
            record.timestamp,
            record.encrypted,
            record.mode,
            record.ipfsCid,
            record.algorithm
        );
    }
}
