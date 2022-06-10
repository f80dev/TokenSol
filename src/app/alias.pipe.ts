import { Pipe, PipeTransform } from '@angular/core';
import {MatSnackBar} from "@angular/material/snack-bar";
import {MetabossService} from "./metaboss.service";
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
    if(typeof value=="string")value=value.toLowerCase();
    for(let k of this.network.keys){
      if(args.length>0 && args[0]=="pubkey"){
        if(k.name.toLowerCase()==value)return k.pubkey;
      }else{
        if(k.pubkey.toLowerCase()==value)return k.name;
      }
    }
    return value;
  }

}
