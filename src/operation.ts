//Description d'une collection
export interface Collection {
  name: string | undefined
  id: string | undefined
  visual: string | undefined
  description: string | undefined
  owner : string | undefined
  price: number | undefined
  type: string | undefined
  roles: any[] | undefined
  link: string | ""

  options: {
    canFreeze: boolean | true
    canWipe: boolean | true
    canPause: boolean | true
    canTransferNFTCreateRole: boolean | true
    canChangeOwner: boolean | true
    canUpgrade: boolean | true
    canAddSpecialRoles: boolean | true
  }
}

export interface Connexion {
  on_device: boolean | false
  address: boolean | false
  wallet_connect: boolean | false
  email: boolean | false
  google: boolean | false
  webcam: boolean | false
  nfluent_wallet_connect: boolean | false            //QRCode proposé par nfluent en substitution de Wallet Connect à utiliser depuis le wallet nfluent
}

export interface Source {
  active: boolean
  type: "database" | "network" | "file"
  connexion: string
  filter: any | null
  owner: string | null
  dbname: string | null
  collections: string[] | null
}



//Description de la structure d'une opération
//Voir le fichier yaml commenté pour le détail des sections
export interface Operation {
  id: string
  title: string
  description: string
  website: string
  version: string
  network: string
  metadatastorage: string
  format: "yamlv1" | "yamlv2"

  collections:Collection[]

  database: any | null
  accounts: any | null

  branding: {
    style: any
  } | null

  new_account: {
    mail: string | ""
    max_account_by_email: number
    to_start: {
      money: string
      bank: string
      amount: number
    } | null
  }

  data: {
    sources: Source[]
  }

  lazy_mining :{
    metadata_storage: string
    content_storage: string
    miner: string
  } | null

  candymachine : {
    visible: boolean
    collections:string[]

    messages:{
      title: string
    }

    limit: {
      total: number
      per_user: number
    }

    connexion: Connexion
  }

  validate:{
    title: string
    visible: boolean
    camera: boolean
    manual_input: boolean

    application: string
    authentification: Connexion

    users: string[]
    support: {
      contacts: {
        message: string
        mail: string
        phone: string
        telegram: string | null
      },
      message_search: string
      warning_process: string
    }

    properties: string[]

    actions:{
      buttons: [
        {
          api: string
          label: string
          n_pass: number
          collections: string[]
        }
      ]

      success : {
        message: string | ""
        api: string | ""
        redirect: string | ""
        redirect_user: string | ""
      }

      fault: {
        message: string | ""
        api: string | ""
        redirect: string | ""
      }
    }

    method:{
      update_token: boolean
      update_authority: boolean
      storage: string
      repository: string | null
    }

    filters: {
      mint_authority: string | null
      collections: string[]
      symbol: string
    }

  } | null

  payment: {
    merchantId: string
    merchantName: string
    currencyCode: string
    countryCode: string
    billing: boolean
  } | null

  store: {
    visible: boolean
    application: string

    filter: null | {
      from: number
      to: number
    }

    collections:{
      name: string
      price: number | null
      limit: number | null
    }[]

    support:any | null


    prestashop: {
      server: string
      address: string
      admin: string
      api_key: string

      root_category: {
        name: string
        description: string
        visual: string
      }

      on_sale: boolean
      language: number
    } | null
  } | null

  nftlive: {
    collections:string[]
    dynamic_fields:[{
      name: string
      maxlen: number | 30
      value: string | ""
      message: string | ""
    }]
    nft_target: {
      collection: string
      name: string
      miner: string
      dimensions: string
      royalties: number
      quality:number | 90

      permissions:{
        transfer: boolean
        update_name: boolean
        update_attributes: boolean
      }
    }

    price: number
    configuration: string
    limit: number

    period:             {
      start:string
      end:  string
    }
  } | null

  event: {
    title: string
    place: string
    dates:[{
      start: string
      end: string
    }]


  } | null

  dispenser: {
    visible: boolean
    application: string
    collections: string[]
    authentification: Connexion
    title: string
    prompt: string
    selfWalletConnection: boolean
  } | null

  airdrop: {
    visible: boolean
    collections: string[]
  } | null

  lottery: {
    image_code: string | ""
    iframe_code: string | ""
    visible: boolean
    miner: string | null
    screen: any
    end_process:{
      winner: {
        message:string
        redirection:string
      }
      looser:{
        message:string
        redirection: string
      }
    }
    authentification: Connexion

    messages:{
      title:string | "Flasher ce QRCode pour recevoir ce NFT"
    } | undefined

    application: string | "$nfluent_appli$/contest"
    collections: [string]
    limits:any | null
    duration:number | 100
    period:{
      dtStart: string | "now"
      dtEnd: string | ""
      duration: number | 1
    }
  } | null

}

export function find_collection(ope:Operation,name:string) : Collection | null {
  for(let c of ope.collections){
    if(c.name==name)return c;
  }
  return null;
}



