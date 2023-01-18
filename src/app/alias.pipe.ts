import { Pipe, PipeTransform } from '@angular/core';
import {NetworkService} from "./network.service";


@Pipe({
  name: 'alias'
})
export class AliasPipe implements PipeTransform {

  constructor(
      public network:NetworkService
  ){}



  transform(value: string | undefined, ...args: unknown[]): string {
    if(!value)return "";
    let comp_value=value;
    if(typeof value=="string")
      comp_value=value.toLowerCase();
    try{
      for(let k of this.network.keys){
        if(args.length>0 && args[0]=="address"){
          if(k.name.toLowerCase()==comp_value)return k.address;
        }else{
          if(k.address.toLowerCase()==comp_value)return k.name;
        }
      }
    } catch (e) {

    }
    return value;
  }

}
