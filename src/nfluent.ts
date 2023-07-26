import {NFLUENT_WALLET} from "./definitions";
import {NFT} from "./nft";
import {ImageItem} from "ng-gallery";
import {setParams, showMessage} from "./tools";
import {_prompt} from "./app/prompt/prompt.component";

export function canTransfer(nft:NFT,address:string) : boolean {
  if(!nft.balances.hasOwnProperty(address))return false;
  if(nft.balances[address]==0)return false;
  return true;
}

export function open_image_banks(vm:any){
  showMessage(vm,"Il est possible de faire directement glisser les images d'un site web vers le calque souhaité")
  _prompt(vm,"Saisissez un mot clé (de préférence en anglais)",
    "rabbit",
    "Accéder directement à plusieurs moteurs de recherche d'image","text",
    "Rechercher","Annuler",false).then((resp:any)=>{
    open("https://www.google.com/search?q=google%20image%20"+resp+"&tbm=isch&tbs=ic:trans","search_google");
    open("https://giphy.com/search/"+resp,"giphy")
    open("https://pixabay.com/fr/vectors/search/"+resp+"/","search_vector")
    open("https://thenounproject.com/search/icons/?iconspage=1&q="+resp,"search_vector")
    open("https://pixabay.com/images/search/"+resp+"/?colors=transparent","search_transparent")
    open("https://www.pexels.com/fr-fr/chercher/"+resp+"/","search_pexels")
  })

}



export function init_visuels(images:any[]){
  return(images.map((x:any)=>{
    return new ImageItem({src:x,thumb:x});
  }));
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
