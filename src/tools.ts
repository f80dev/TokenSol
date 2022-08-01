import {environment} from "./environments/environment";
import {ActivatedRoute} from "@angular/router";

export interface MetabossKey {
  name: string
  pubkey: string
  privatekey:string | null
  encrypt:string | null
  balance:number | null
  qrcode:string | null
  explorer:string | null
  unity:string | null
}

export function encrypt(s:string) : string {
  return btoa(s);
}

export function setParams(_d:any,prefix="") : string {
  let rc=[];
  for(let k of Object.keys(_d)){
    if(typeof(_d[k])=="object")_d[k]="b64:"+btoa(JSON.stringify(_d[k]));
    rc.push(k+"="+_d[k]);
  }
  return encrypt(prefix+rc.join("&"));
}

export function getParams(routes:ActivatedRoute) {
  return new Promise((resolve, reject) => {
    routes.queryParams.subscribe(params => {
      if(params.hasOwnProperty("param")){
        let _params=decrypt(params["param"]).split("&");
        let rc:any={};
        for(let _param of _params){
          let key=_param.split("=")[0];
          let value=_param.split("=")[1];

            $$("Récupération de "+_param);

            if(value.startsWith("b64:"))value=JSON.parse(atob(value.replace("b64:","")));
            if(value=="false")resolve(false);
            if(value=="true")resolve(true);
            rc[key]=value;
        }
        resolve(rc);
      } else {
          resolve(params);
      }
    },(err)=>{reject(err);})
  });
}

export function decrypt(s:string | any) : string {
  if(s)
    return atob(s);

  return "";
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

export function isLocal(domain:string) : boolean {
  return(domain.indexOf("localhost")>-1 || domain.indexOf("127.0.0.1")>-1);
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

export function hasWebcam(result:boolean) {
  navigator.mediaDevices.enumerateDevices().then((devices:any)=>{
    result=false;
    for(let device of devices)
      if(device.kind=="videoinput")result=true;
  })
}


export function showError(vm:any,err:any=null){
  $$("!Error ",err);
  if(vm && vm.hasOwnProperty("message"))vm.message="";
  let mes="Oops, un petit problème technique. Veuillez recommencer l'opération";
  if(err && err.hasOwnProperty("error"))mes=err.error;
  showMessage(vm,mes);
}

export function base64ToArrayBuffer(base64:string) : ArrayBuffer {
  var binary_string = atob(base64);
  var len = binary_string.length;
  var bytes = new Uint8Array(len);
  for (var i = 0; i < len; i++) {
    bytes[i] = binary_string.charCodeAt(i);
  }
  return bytes.buffer;
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

export function detect_network(addr:string){
  if(addr.length<20 || addr.indexOf("@")>-1)return null;
  if(addr.startsWith("erd"))return "elrond";
  return "solana";
}

export function detect_type_network(network:string){
  if(network.indexOf("devnet")>-1)return "devnet";
  return "mainnet";
}

