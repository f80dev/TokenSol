import {environment} from "./environments/environment";
import {stringify} from "querystring";

export interface MetabossKey {
  name: string
  pubkey: string
  privatekey:string | null
}

export function toStringify(obj:any) {
  return JSON.stringify(obj, (key, value) =>
    typeof value === 'bigint'
      ? value.toString()
      : value // return everything else unchanged
  );
}

export function getExplorer(addr: string | undefined,network="solana-devnet") {
  return "https://solscan.io/account/"+addr+"?cluster="+network.replace("solana-","");
}

export function syntaxHighlight(json:any) {
  if (typeof json != 'string') {
    json = JSON.stringify(json, undefined, 2);
  }
  json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, (match:any)=> {
    var cls = 'number';
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'key';
      } else {
        cls = 'string';
      }
    } else if (/true|false/.test(match)) {
      cls = 'boolean';
    } else if (/null/.test(match)) {
      cls = 'null';
    }
    return '<span class="' + cls + '">' + match + '</span>';
  });
}


export function removeBigInt(obj:any) {
  Object.keys(obj).map((key:any, index:any) =>
    typeof obj[key] === 'bigint'
      ? obj[key] .toString()
      : obj[key]  // return everything else unchanged
  );

  return obj;
}

// @ts-ignore
/**
 * Affichage du message
 * @param vm
 * @param s
 * @param duration
 * @param func
 * @param label_button
 */
export function showMessage(vm:any,s:string="",duration=4000,func:any= null,label_button="ok"){
  if(s==null || s.length==0)return false;
  s=s+"";
  $$("Affichage du message :",s)
  if(s.startsWith("#")){
    //Affichage en mode plein écran
    s=s.substr(1);
    vm.message=s;
    if(s.length>0)setTimeout(()=>{vm.showMessage=true;},500);
  } else {
    //Affichage en mode toaster
    if(vm){
      var toaster=vm.toast || vm.snackBar || vm.toaster;
      if(toaster!=null){
        if(func){
          toaster.open(s,label_button,{duration:duration}).onAction().subscribe(()=>{
            func();
          });
        }
        else
          toaster.open(s,"",{duration:duration});
      }
    }
  }
  return true;
}


export function words(objs:any,rc=""){
  if(!objs)return rc;
  for(let it of Object.values(objs)) {
    while(typeof it=="object"){
      // @ts-ignore
      it=Object.values(it).join(" ").toLowerCase();
    }
    rc=rc+it+" ";
  }
  return rc;
}


export function showError(vm:any,err:any=null){
  $$("!Error ",err);
  if(vm && vm.hasOwnProperty("message"))vm.message="";
  let mes="Oops, un petit problème technique. Veuillez recommencer l'opération";
  if(err && err.hasOwnProperty("error"))mes=err.error;
  showMessage(vm,mes);
}




export function $$(s: string, obj: any= null) {
  console.log("");
  if(environment.production)return;
  if((s!=null && s.startsWith("!")) || localStorage.getItem("debug")=="1"){
    //debugger
  }
  const lg = new Date().getHours() + ':' + new Date().getMinutes() + ' -> ' + s;
  if (obj != null) {
    obj = JSON.stringify(obj);
  } else {
    obj = '';
  }
  console.log(lg + ' ' + obj);
  if (lg.indexOf('!!') > -1  || localStorage.getItem("debug")=="2") {alert(lg); }
}

