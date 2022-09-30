
export interface Layer {
  params: any;
  unique: boolean
  indexed: boolean
  name:string
  position:number
  elements:any[]
  text:string
  translation: {
    x:number | 0
    y:number | 0
  }
  scale:{
    x:number | 1
    y:number | 1
  }
}
