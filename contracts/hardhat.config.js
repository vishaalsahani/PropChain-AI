require("@nomicfoundation/hardhat-ethers");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: { enabled: true, runs: 200 },
    },
  },
  paths: {
    sources: "./src",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  networks: {
    // In-process chain used by `hardhat test`
    hardhat: { chainId: 31337 },
    // Local node started with `npm run node` (also used by the backend via RPC)
    localhost: { url: "http://127.0.0.1:8545", chainId: 31337 },
  },
};
