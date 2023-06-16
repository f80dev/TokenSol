// This file can be replaced during build by using the `fileReplacements` array.
// `ng build` replaces `environment.ts` with `environment.prod.ts`.
// The list of file replacements can be found in `angular.json`.

import {newCryptoKey} from "../tools";

export const environment = {
  production: false,
  mail:"contact@nfluent.io",
  forum:"",
  version: "dev",
  server:"http://127.0.0.1:4242",
  appname:"TokenForge",
  visual:"./assets/forge.jpg",
  claim:"From design to implementation",
  appli:"http://127.0.0.1:4200",
  wallet:"http://127.0.0.1:4200",
  website:"https://nfluent.io",
  logo:"./assets/icons/tokenforge-512.png",

  stockage: "server-nfluent,nftstorage,infura,github-nfluentdev-storage-main",
  stockage_document: "server-nfluent,github-nfluentdev-storage-main,infura,server",
  networks_available:"elrond-devnet,polygon-devnet,db-server-nfluent",

  admin:{
    default_miner:"dudule: Z0FBQUFBQmtWUUdEa2FCdHdVeHRnaFlsRDVlMUJHbDlEWi0tVlVjMGF4Qmk2VWpjbXd1LW1JQ3poQzMtbFN2YzdtT3BLSk9PY2gxRElBLTFXYlZ0NTdvakI3NXVJUjN3SUVxS0N3Q3lQa1F5eks4VmhNZ0p2QWJmN3Y3bV9lVXViRmdXSFJTWjBQN0pWOV9vWHNUWGNoN0lMRFB1dDI3TFB3OHp1dzAxWmphSnhXLUFRa2pGX3VYMHlPMTR0TTZ3MXFYcVJDakVxenJGbGlZYm05MndPVXo5Q2w0U05qdGM5S29xMWdyRmtIWlFoQ3hKTEYtMVdfTk85M2NsV2NKWlRVWkFIeEJNdWkwSGFnaGpZVVBBTFNXMmlBeWhPXzVHT3hTVUYzRkIxQVlYQkxyaFcxUUpIQkdlSzlVekg4QjIwWWNDSkVLZUlKU2NFVnVmdHdsMjREMlVpOVpUWE91SHFOc2hIUndiSUtUQVBXRDJhNXEwdmFjbC1CcE90VVlYUzVrelRHbzlCTmZvdTVhTHMwQS1DOGtvdGhJRVE5ckRRX1liRHpYMEZSNzktdFZKeENJamtSdTBmNTh6OVVTSVdYUEtYcXk2UGVuUA==",
    default_collection: "MACOL0XF-f53101",
    default_networks:"elrond-devnet,polygon-devnet",
    default_price:1,
    default_fiat_price:0.1
  },

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
    price_in_fiat: 0,
    price_in_crypto: 0
  },

  bank:{
    miner: newCryptoKey("","","","nfluent: Z0FBQUFBQmtYUjJVbS1Uc0lpa2FTR2F0SnF4LW1HUHIzbHFKN2hCVmRPN3NRR1R3Wk4tUnhfcUxqUE9IQVdObzMxMHgtazhrT1hpWXVndENZallGNnI1Q2RTLVQ1N2d0TEQ2dHNmVlByV3B0RlR3SUMxejhKMHZUeVJ3NHl6dnNFNEIyZWk2eGZsS1hWU2FuQnljcGRDUEh4WFhSMTBRTFFLdHkxeTJuUjZxYWRRc1dVN2FqYlZzPQ=="),
    title:"Bienvenu a la banque des NFluCoin",
    refund:5,
    token:"NFLUCOIN-4921ed",
    network:"elrond-devnet",
    limit:5,
    histo:"db-server-nfluent",
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
          unity: "NfluCoin",
        }

  },

  dictionnary: {}
};

/*
 * For easier debugging in development mode, you can import the following file
 * to ignore zone related error stack frames such as `zone.run`, `zoneDelegate.invokeTask`.
 *
 * This import should be commented out in production mode because it will have a negative impact
 * on performance if an error is thrown.
 */
// import 'zone.js/plugins/zone-error';  // Included with Angular CLI.
