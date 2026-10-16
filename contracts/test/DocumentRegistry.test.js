const { expect } = require("chai");
const { ethers } = require("hardhat");

const HASH_A = ethers.keccak256(ethers.toUtf8Bytes("propchain demo document"));
const HASH_B = ethers.keccak256(ethers.toUtf8Bytes("tampered copy of the document"));

describe("DocumentRegistry", function () {
  it("registers a document hash and verifies a matching hash", async function () {
    const registry = await ethers.deployContract("DocumentRegistry");
    await registry.registerDocument(1, HASH_A);
    expect(await registry.verifyDocument(1, HASH_A)).to.equal(true);
  });

  it("fails verification for a different hash (tamper case)", async function () {
    const registry = await ethers.deployContract("DocumentRegistry");
    await registry.registerDocument(1, HASH_A);
    expect(await registry.verifyDocument(1, HASH_B)).to.equal(false);
  });

  it("rejects a second registration for the same document id", async function () {
    const registry = await ethers.deployContract("DocumentRegistry");
    await registry.registerDocument(7, HASH_A);

    let reverted = false;
    try {
      await registry.registerDocument(7, HASH_B);
    } catch (err) {
      reverted = String(err.message).includes("Already registered");
    }
    expect(reverted).to.equal(true);
  });

  it("stores record metadata (hash, uploader, timestamp, exists)", async function () {
    const [signer] = await ethers.getSigners();
    const registry = await ethers.deployContract("DocumentRegistry");
    await registry.registerDocument(42, HASH_A);

    const record = await registry.records(42);
    expect(record.fileHash).to.equal(HASH_A);
    expect(record.uploader).to.equal(signer.address);
    expect(record.exists).to.equal(true);
    expect(Number(record.timestamp)).to.be.greaterThan(0);
    expect(await registry.recordCount()).to.equal(1n);
  });

  it("emits DocumentRegistered on registration", async function () {
    const [signer] = await ethers.getSigners();
    const registry = await ethers.deployContract("DocumentRegistry");

    const receipt = await (await registry.registerDocument(9, HASH_A)).wait();
    const events = receipt.logs
      .map((log) => {
        try {
          return registry.interface.parseLog(log);
        } catch {
          return null;
        }
      })
      .filter(Boolean);

    const event = events.find((e) => e.name === "DocumentRegistered");
    expect(event).to.not.equal(undefined);
    expect(event.args.documentId).to.equal(9n);
    expect(event.args.fileHash).to.equal(HASH_A);
    expect(event.args.uploader).to.equal(signer.address);
    expect(Number(event.args.timestamp)).to.be.greaterThan(0);
  });
});
