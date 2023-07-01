import { Pipe, PipeTransform } from '@angular/core';
import {environment} from "../environments/environment";

@Pipe({
  name: 'translate'
})
export class TranslatePipe implements PipeTransform {


  transform(value: string | undefined, ...args: string[]): string {
    let result="";
    if(!value)return "";
    let lang=args.length>0 ? args[0].toLowerCase() :  navigator.language.split("-")[0];
    if(lang.length>2)lang= navigator.language.split("-")[0];
    if(lang=="us")lang="en";

    if(typeof(value)=="string"){
      if(!environment.dictionnary.hasOwnProperty(lang))return value;
      // @ts-ignore
      let dict:any=environment.dictionnary[lang] || environment.dictionnary["en"];
      if(!dict){
        result=value;
      } else {
        result=dict[value] || dict[value.toLowerCase()];
        if(!result)result=value;
      }
    }
    else{
      result=value
    }

    for(let i=1;i<args.length;i++){
      result=result.replace("#"+i,args[i])
    }
    return result;

  }
}
