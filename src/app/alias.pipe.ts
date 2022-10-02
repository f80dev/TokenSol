import { Pipe, PipeTransform } from '@angular/core';
import {MetabossService} from "./metaboss.service";


@Pipe({
  name: 'alias'
})
export class AliasPipe implements PipeTransform {

  constructor(
      public metaboss:MetabossService
  ){}



  transform(value: string | undefined, ...args: unknown[]): string {
    if(!value)return "";
    let comp_value=value;
    if(typeof value=="string")
      comp_value=value.toLowerCase();
    try{
      for(let k of this.metaboss.keys){
        if(args.length>0 && args[0]=="pubkey"){
          if(k.name.toLowerCase()==comp_value)return k.pubkey;
        }else{
          if(k.pubkey.toLowerCase()==comp_value)return k.name;
        }
      }
    } catch (e) {

    }
    return value;
  }

}
