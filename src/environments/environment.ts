// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

export const environment = {
  production: false,
  mail:"contact@nfluent.io",
  forum:"",
  version: "dev",
  server:"http://127.0.0.1:4242",
  appname:"TokenForge",
  splash_visual:"./assets/forge.jpg",
  claim:"From design to implementation",
  appli:"http://127.0.0.1:4200",
  wallet:"http://127.0.0.1:4200",
  website:"https://nfluent.io",
  stockage: "server-nfluent,nftstorage,infura,github-nfluentdev-storage-main",
  stockage_document: "server-nfluent,github-nfluentdev-storage-main,infura,server",
  networks_available:"elrond-devnet,polygon-devnet,db-server-nfluent_local",

  mint_cost:{
    price_to_mint_one_token_in_crypto:0.5,
    price_to_mint_one_token_in_fiat:0.1
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
          unity: "NfluCoin"
        }

  }
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
