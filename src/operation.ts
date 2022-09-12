//Description d'une collection
export interface Collection {
  name: string
  visual: string
  description: string
  creator: string
  price: number
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

  collections:Collection[]

  database: any | null
  accounts: any | null

  branding: {
    style: any
  } | null

  data: {
    sources: {
      type: string
      connexion: string
      filter: any | null
      owner: string | null
      dbname: string | null
    }[]
  }

  lazy_mining :{
    metadata_storage: string
    content_storage: string
    network: string
    miner: string
  }

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
  }

  validate:{
    title: string
    visible: boolean
    camera: boolean
    manual_input: boolean

    application: string

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
        message: string
        api: string
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

  dispenser: {
    visible: boolean
    miner: string
    application: string

    collections:       {
      name: string
      limit: number
    }[]
  } | null

  lottery: any | null

}

export function find_collection(ope:Operation,name:string) : Collection | null {
  for(let c of ope.collections){
    if(c.name==name)return c;
  }
  return null;
}



