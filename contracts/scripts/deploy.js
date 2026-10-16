const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const registry = await hre.ethers.deployContract("DocumentRegistry");
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  const network = await hre.ethers.provider.getNetwork();
  const chainId = network.chainId.toString();

  console.log(`DocumentRegistry deployed to ${address} (chainId ${chainId}, network ${hre.network.name})`);

  const outDir = path.join(__dirname, "..", "deployments");
  fs.mkdirSync(outDir, { recursive: true });
  const outFile = path.join(outDir, `${hre.network.name}.json`);
  fs.writeFileSync(
    outFile,
    JSON.stringify(
      {
        contract: "DocumentRegistry",
        address,
        chainId,
        network: hre.network.name,
        deployedAt: new Date().toISOString(),
      },
      null,
      2
    )
  );
  console.log(`Deployment info written to ${outFile}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
