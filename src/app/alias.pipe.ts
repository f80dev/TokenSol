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

  transform(value: string | undefined, ...args: unknown[]): unknown {
    for(let k of this.network.keys){
      if(k.pubkey==value)return k.name;
    }
    return value;
  }

}
