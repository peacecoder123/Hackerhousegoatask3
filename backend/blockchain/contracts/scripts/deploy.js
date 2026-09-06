const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying FaceChainVerify to Sepolia...");

  const FaceChainVerify = await ethers.getContractFactory("FaceChainVerify");
  const contract = await FaceChainVerify.deploy();
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log(`✅ FaceChainVerify deployed to: ${address}`);
  console.log(`\nAdd this to your .env file:\nCONTRACT_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
