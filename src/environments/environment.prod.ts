export const environment = {
  production: true,
  mail:"contact@nfluent.io",
  forum:"",
  version: "0.1.57",
  claim:"From design to implementation",
  server:"https://api.nfluent.io:4242",
  appname:"TokenForge",
  splash_visual:"./assets/forge.jpg",
  appli:"https://tokenforge.nfluent.io",
  wallet:"https://wallet.nfluent.io",
  website:"https://nfluent.io",
  stockage: "server-nfluent,nftstorage,infura,github-nfluentdev-storage-main",
  stockage_document: "server-nfluent,github-nfluentdev-storage-main,infura,server",
  networks_available:"elrond-devnet,polygon-devnet,db-server-nfluent",

  mint_cost:{
    price_to_mint_one_token_in_crypto:0.1,
    price_to_mint_one_token_in_fiat:0.01
  },

  collection_cost:{
    price_in_fiat: 1,
    price_in_crypto: 5
  },
  visual_cost:{
    quota: 20,
    price_in_fiat: 0.001,
    price_in_crypto: 0.01
  },

  merchant:{
    id:"BCR2DN4TYD4Z5XCR",
    name:"NFluenT",
    currency:"EUR",
    country:"FR",
    contact:"contact@nfluent.io",
    wallet:
        {
          token:"NFLUCOIN-4921ed",
          address:"erd1gkd6f8wm79v3fsyyklp2qkhq0eek28cnr4jhj9h87zwqxwdz7uwstdzj3m",
          network:"elrond-devnet",
          unity: "NfluCoint"
        }
  }
};

//server:"https://server.f80lab.com:4242",
//appli:"https://tokenfactory.nfluent.io",
