//Description d'une collection
import {CryptoKey} from "./tools";




export interface Collection {
  gallery: any;
  name:string
  id: string
  cover:string | undefined
  visual: string | undefined
  description: string | undefined
  owner : CryptoKey | string
  price: number | undefined
  type: string | undefined
  roles: any[] | undefined
  link: string | ""
  supply: number
  options: string[] | []
}

export interface Connexion {
  on_device: boolean | false
  address: boolean | false
  keystore: boolean | false
  wallet_connect: boolean | false
  email: boolean | false
  google: boolean | false
  webcam: boolean | false
  extension_wallet:boolean | false
  web_wallet:boolean | false
  private_key:boolean | false
  direct_connect: boolean | false
  nfluent_wallet_connect: boolean | false            //QRCode proposé par nfluent en substitution de Wallet Connect à utiliser depuis le wallet nfluent
}

export interface Source {
  active: boolean
  type: "database" | "network" | "file"
  connexion: string
  filter: any | null
  miner: CryptoKey | null
  dbname: string | null
  collections: string[] | null
}

//Section contenant les différents messages affiché aux clients
export interface Messages {
  confirm: string
  title: string
  subtitle: string | ""
  prompt: string | null
  cancel: string | null
  question: string | null
  help: string | ""             //Lien internet pointant vers une aide
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
  warning: string | ""                //Message sur l'opération elle-même (problème de syntaxe par exemple ou solde insuffisant)

  collections:Collection[]

  database: {
    connexion: string
    dbname: string
  } | null
  accounts: any | null

  branding: {
    appname:string
    splash_visual: string
    claim:string | ""
    style: any | {}
    reverse_card: any | {}
  }

  new_account: {
    mail: string | ""
    max_account_by_email: number
    to_start: {
      money: string
      bank: string
      amount: number
    } | null
  }

  transfer : {
    mail: string | ""
  }

  data: {
    sources: Source[]
  }

  mining :{
    metadata_storage: string
    content_storage: string
    networks:[{
        network: string
        miner: CryptoKey
        collection: string
      }]
  } | null

  candymachine : {
    visible: boolean
    collections:string[]

    messages: Messages

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

    apparence: {
      size: string
      fontsize: string
    }

    collections:{
      name: string
      price: number | null
      limit: number | null
    }[]

    support:any | null

    messages: Messages

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
      miner: CryptoKey
      dimensions: string
      royalties: number
      configuration: string
      quality:number | 90

      permissions:{
        transfer: boolean
        update_name: boolean
        update_attributes: boolean
      }
    }

    price: number
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

    mailing_list: boolean | true

    messages: Messages

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

    messages: Messages

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

  nfts : [{
    storage: string
    data: string
  }]

}

export function newCollection(name:string,owner:CryptoKey,id="",type_collection="SemiFungible") : Collection {
  if(id.length==0)id=name;
  return {
    description: "",
    id: id,
    gallery:true,
    link: "",
    name: name,
    supply:1,
    cover:"",
    options: [],
    owner: owner,
    price: 0,
    roles: undefined,
    type: type_collection,
    visual: undefined
  }
}

export function find_collection(ope:Operation,name:string) : Collection | null {
  for(let c of ope.collections){
    if(c.name==name)return c;
  }
  return null;
}

//Permet d'extraire des informations d'une operation de facçon simple (moins de code)
export function get_in(obj:any | null,fields:string,_default:any=null) : any {
  if(!obj)return _default;

  let rc={...obj};
  for(let field of fields.split(".")){
    if(rc.hasOwnProperty(field)){
      // @ts-ignore
      rc=rc[field];
    }else{
      return _default;
    }
  }
  return rc;
}


export function check_nft(ope:Operation){
  let checknft=get_in(ope,"validate.filters.collections",get_in(ope,"validate.collections",[]))
  if(checknft.length==0){
    //Recherche de collection dans les sources
    for(let src of ope.data.sources){
      checknft=get_in(src,"collection",get_in(src,"filter.collection",[]))
      if(checknft.length>0)break
    }
    if(checknft.length==0){
      //Recherche de collection dans le lazy_mining
      for(let network of get_in(ope,"lazy_mining.networks",[])){
        checknft=get_in(network,"collection",[])
        if(checknft.length>0)break;
      }
    }
  }
}



