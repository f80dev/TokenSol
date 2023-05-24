import {environment} from "./environments/environment";
import {ActivatedRoute} from "@angular/router";
import {NFT} from "./nft";
import {Clipboard} from "@angular/cdk/clipboard";
import {NFLUENT_WALLET} from "./definitions";
import {ImageItem} from "ng-gallery";

export interface CryptoKey {
  name: string | null
  address: string
  privatekey:string | null
  encrypt:string | undefined
  balance:number | null
  qrcode:string | null
  explorer:string | null
  unity:string | null
}

export function newCryptoKey(address="",name="",privateKey="",encrypted:string | undefined=undefined) : CryptoKey {
  let rc:CryptoKey= {
    explorer:null, qrcode: "", unity: "",
    name:name,
    address:address,
    privatekey:privateKey,
    encrypt:encrypted,
    balance:null
  }
  return rc
}

export function url_wallet(network:string) : string {
  if(network.indexOf("elrond")>-1){
    return network.indexOf("devnet")==-1 ? "https://wallet.elrond.com" : "https://devnet-wallet.elrond.com";
  } else {
    return "";
  }
}

export function get_nfluent_wallet_url(address:string,network:string,domain_appli:string=NFLUENT_WALLET,take_photo=false,) : string {
  let url=domain_appli+"/?"+setParams({
    toolbar:false,
    address:address,
    takePhoto:take_photo,
    network:network
  })
  url=url.replace("//?","/?");
  return url;
}


export function hashCode(s:string):number {
  var hash = 0,
    i, chr;
  if (s.length === 0) return hash;
  for (i = 0; i < s.length; i++) {
    chr = s.charCodeAt(i);
    hash = ((hash << 5) - hash) + chr;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}


export function b64DecodeUnicode(s:string):string {
  return decodeURIComponent(Array.prototype.map.call(atob(s), function(c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
  }).join(''))
}

export function encodeUnicode(str:string) {
  // first we use encodeURIComponent to get percent-encoded UTF-8,
  // then we convert the percent encodings into raw bytes which
  // can be fed into btoa.
  return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
    function toSolidBytes(match, p1) {
      return String.fromCharCode(Number('0x' + p1));
    }));
}


export function encrypt(s:string) : string {
  //TODO fonction a terminer
  return btoa(s);
}


export function getBrowserName() {
  const agent = window.navigator.userAgent.toLowerCase()
  switch (true) {
    case agent.indexOf('edge') > -1:
      return 'edge';
    case agent.indexOf('opr') > -1 && !!(<any>window).opr:
      return 'opera';
    case agent.indexOf('chrome') > -1 && !!(<any>window).chrome:
      return 'chrome';
    case agent.indexOf('trident') > -1:
      return 'ie';
    case agent.indexOf('firefox') > -1:
      return 'firefox';
    case agent.indexOf('safari') > -1:
      return 'safari';
    default:
      return 'other';
  }
}


export function setParams(_d:any,prefix="",param_name="p") : string {
  //Encryptage des parametres de l'url
  //Version 1.0
  let rc=[];
  for(let k of Object.keys(_d)){
    if(typeof(_d[k])=="object")_d[k]="b64:"+btoa(JSON.stringify(_d[k]));
    rc.push(k+"="+encodeURIComponent(_d[k]));
  }
  let url=encrypt(prefix+rc.join("&"));
  if(param_name!="")
    return param_name+"="+encodeURIComponent(url);
  else
    return encodeURIComponent(url);
}


export function analyse_params(params:string):any {
  let _params=decrypt(decodeURIComponent(params)).split("&");
  $$("Les paramètres à analyser sont "+_params);
  let rc:any={};
  for(let _param of _params) {
    let key = _param.split("=")[0];
    let value: any = decodeURIComponent(_param.split("=")[1]);

    $$("Récupération de " + _param);
    if (value.startsWith("b64:")) {
      try {
        value = JSON.parse(atob(value.replace("b64:", "")));
      } catch (e) {
        $$("!Impossible de parser le paramétrage");
      }
    }
    if (value == "false") value = false;
    if (value == "true") value = true;
    rc[key] = value;

    if(key=="params_file"){
      fetch(environment.server+"/api/yaml/?file="+value).then((content:any)=>{
        debugger
      })
    }

  }
  return rc;
}

export function now(format="number") : any {
  let rc=new Date().getTime();
  if(format=="date")return new Date().toLocaleDateString();
  if(format=="time")return new Date().toLocaleTimeString();
  if(format=="datetime")return new Date().toLocaleString();
  if(format=="rand")return (Math.random()*10000).toString(16);
  if(format=="hex")return rc.toString(16);
  if(format=="dec" || format=="str")return rc.toString();
  return rc
}


export function exportToCsv(filename: string, rows: object[]) {
  if (!rows || !rows.length) {
    return;
  }
  const separator = ',';
  const keys = Object.keys(rows[0]);
  const csvContent =
      keys.join(separator) +
      '\n' +
      rows.map((row:any) => {
        return keys.map(k => {
          let cell = row[k] === null || row[k] === undefined ? '' : row[k];
          cell = cell instanceof Date
              ? cell.toLocaleString()
              : "'"+cell.toString().replace(/"/g, '""')+"'";
          if (cell.search(/("|,|\n)/g) >= 0) {
            cell = `"${cell}"`;
          }
          return cell;
        }).join(separator);
      }).join('\n');

      download_file(csvContent,filename)
}

export function init_visuels(images:any[]){
  return(images.map((x:any)=>{
    return new ImageItem({src:x,thumb:x});
  }));
}

//tag #save_file save local
export function download_file(content:string,filename:string,_type='text/csv;charset=utf-8;'){
  const blob = new Blob([content], { type: _type });
  const link = document.createElement('a');
  if (link.download !== undefined) {
    // Browsers that support HTML5 download attribute
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}


function drawRotated(canvas:any, image:any, degrees:any) {
  var ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(canvas.width / 2, canvas.height / 2);
  ctx.rotate(degrees * Math.PI / 180);
  ctx.drawImage(image, -image.width / 2, -image.height / 2);
  ctx.restore();
}



/**
 *
 * @param src
 * @param angle
 * @param quality
 * @param func
 */
export function rotate(src: string, angle: number, quality: number=1) : Promise<string> {
  return new Promise((resolve) => {
    if (angle == 0)
      resolve(src);
    else {
      var img = new Image();
      img.onload = function() {
        var canvas:any = document.createElement('canvas');
        canvas.width = img.height;
        canvas.height = img.width;
        drawRotated(canvas, this, angle);
        var rc = canvas.toDataURL("image/jpeg", quality);
        resolve(rc);
      };
      img.src = src;
    }
  });
}


export function apply_params(vm:any,params:any,env:any){
  for(let prop of ["claim","title","appname","background","visual"]){
    if(vm.hasOwnProperty(prop))vm[prop]=params[prop] || env[prop] || "";
  }

  if(vm.hasOwnProperty("network")){
    if(typeof vm.network=="string")vm.network = params.networks || env.network || "elrond-devnet"
  }
  if(params.hasOwnProperty("advanced_mode"))vm.advanced_mode=(params.advanced_mode=='true');

  if(vm.hasOwnProperty("device")){
    vm.device.setTitle(params.appname);
    if(params.favicon)vm.device.setFavicon(params.favicon || "favicon.ico");
  }

  if(params.style && vm.hasOwnProperty("style"))vm.style.setStyle("theme",params.style);
  if(vm.hasOwnProperty("miner"))vm.miner = newCryptoKey("","","",params.miner || env.miner)


}


export function getParams(routes:ActivatedRoute,local_setting_params="",force_treatment=false) {
  //Decryptage des parametres de l'url
  //Version 1.0
  return new Promise((resolve, reject) => {
    setTimeout(()=>{

      routes.queryParams.subscribe((params:any) => {
        if(params==null && local_setting_params.length>0)params=localStorage.getItem(local_setting_params)

        if(params){
          if(params.hasOwnProperty("p")){
            params=analyse_params(decodeURIComponent(params["p"]));
            $$("Analyse des paramètres par la fenetre principale ", params);
          }
        }

        if(!params) {
          if (force_treatment) {resolve({})}else{reject()}
        }else{
          if(local_setting_params.length>0)localStorage.setItem(local_setting_params,params["p"]);
          resolve(params);
        }
      },(err)=>{
        $$("!Impossible d'analyser les parametres de l'url");
        reject(err);
      })
    },200);
  });
}

export function decrypt(s:string | any) : string {
  if(s)return atob(s);
  return "";
}


export function toStringify(obj:any) {
  return JSON.stringify(obj, (key, value) =>
    typeof value === 'bigint'
      ? value.toString()
      : value // return everything else unchanged
  );
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
    s=s.substring(1);
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


export function normalize(s:string) : string {
  return s.toLowerCase().replace(" ","").split(".")[0]
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
  if((s!=null && s.startsWith("!"))){
    //debugger
  }
  const lg = new Date().getHours() + ':' + new Date().getMinutes() + ' -> ' + s;
  if (obj != null) {
    obj = JSON.stringify(obj).replace(",",",\n");
  } else {
    obj = '';
  }
  console.log(lg + ' ' + obj);
  if (lg.indexOf('!!') > -1) {alert(lg); }
}


export function copyAchievements(clp:Clipboard,to_copy:string) {
  return new Promise((resolve, reject) => {
    const pending = clp.beginCopy(to_copy);
    let remainingAttempts = 3;
    const attempt = () => {
      const result = pending.copy();
      if (!result && --remainingAttempts) {
        setTimeout(()=>{
          resolve(true);
        });
      } else {
        // Remember to destroy when you're done!
        pending.destroy();
      }
    };
  });

}

export function canTransfer(nft:NFT) : boolean {
  if(nft.balances[nft.miner.address]==0)return false;
  return true;
}


export function find_miner_from_operation(operation:any,addr:string) : any {
  let to_network=isEmail(addr) ? operation.mining?.networks[0].network : detect_network(addr);  //Si l'adresse est email on prend la première source du mining
  for(let n of operation.mining!.networks){
    if(n.network.startsWith(to_network)){
      return n;
    }
  }
  return {}
}




export function find(liste:any[],elt_to_search:any,index_name:any=0){
  let rc=0;
  for(let item of liste){
    if(typeof elt_to_search=="object") {
      if (item[index_name] == elt_to_search[index_name]) return rc;
    } else {
      if(item[index_name]==elt_to_search) return rc;
    }
    rc=rc+1;
  }
  return -1;
}

//Alias find_network et get_network
export function detect_network(addr:string) : string {
  if(addr.length<20 || addr.indexOf("@")>-1)return "";
  if(addr.startsWith("erd"))return "elrond";
  if(addr.length>50 && addr.endsWith("="))return "access_code";
  return "solana";
}

export function detect_type_network(network:string){
  if(network.indexOf("devnet")>-1)return "devnet";
  return "mainnet";
}

export function jsonToList(obj:any):string {
  let rc="<ul>";
  for(let k of Object.keys(obj)){
    rc=rc+"<li><strong>"+k+"</strong>: "+obj[k]+"</li>"
  }
  return rc+"</ul>";
}


export function isEmail(addr="") {
  if(!addr)return false;
  const expression: RegExp = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
  return expression.test(addr);
}



export interface Bank {
  miner:CryptoKey
  refund: number  //Montant de rechargement
  title: string
  network: string
  token: string
  limit:number //Limit de rechargement par jour
  histo: string //Base de données de stockage de l'historique des transactions
}

export function convert_to_list(text:string="",separator=",") : string[] {
  if(!text)return [];
  if(typeof text!="string")return text;
  text=text.trim()
  if(text.length==0)return [];
  return text.split(",");
}

export function extract_bank_from_param(params:any) : Bank | undefined {
  if(params && params["bank.miner"] && params["bank.token"]){
    return {
      miner: newCryptoKey("","","",params["bank.miner"]),
      network: params["bank.network"],
      refund: params["bank.refund"],
      title: params["bank.title"],
      token: params["bank.token"],
      limit: params["bank.limit"],
      histo:params["bank.histo"],
    }
  }

  return undefined;
}
