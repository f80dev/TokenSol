import {environment} from "./environments/environment";


export function toStringify(obj:any) {
  return JSON.stringify(obj, (key, value) =>
    typeof value === 'bigint'
      ? value.toString()
      : value // return everything else unchanged
  );
}


export function removeBigInt(obj:any) {
  Object.keys(obj).map((key:any, index:any) =>
    typeof obj[key] === 'bigint'
      ? obj[key] .toString()
      : obj[key]  // return everything else unchanged
  );

  return obj;
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

