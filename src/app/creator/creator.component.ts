import {Component, OnDestroy, OnInit} from '@angular/core';

import {NetworkService} from "../network.service";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {
  $$,
  download_file,
  getParams,
  hashCode,
  isLocal,
  normalize,
  now,
  setParams,
  showError,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from "@angular/common";
import {MatSelectChange} from "@angular/material/select";
import {Clipboard} from "@angular/cdk/clipboard";
import {UserService} from "../user.service";
import {Configuration, Layer} from "../../create";
import {OperationService} from "../operation.service";
import {parse, stringify} from "yaml";
import {DeviceService} from "../device.service";
import {wait_message} from "../hourglass/hourglass.component";
import {_ask_for_paiement} from "../ask-for-payment/ask-for-payment.component";
import {extract_merchant_from_param, Merchant} from "../payment/payment.component";


@Component({
  selector: 'app-creator',
  templateUrl: './creator.component.html',
  styleUrls: ['./creator.component.css']
})
//test : http://localhost:4200/creator

export class CreatorComponent implements OnInit,OnDestroy {
  backcolor="lighgray";

  platforms=null;

  url_collection="";
  show_addtext:any;
  configs:Configuration[]=[];
  previews:any[]=[];
  formats=[{label:"webp",value:"webp"},{label:"gif",value:"gif"}]
  sel_ext:{ label:string,value:string }=this.formats[0];
  sel_palette: string="purple";
  palette_names: string[]=[];
  usePalette: boolean=false;
  sel_colors: any[]=[];
  upload_files=[];
  max_nft=0;

  // samples=[
  //   {
  //     label: "paysage",
  //     value: {
  //       layers: [
  //       {
  //         name: 'paysage', files: [
  //           "https://images.pexels.com/photos/2662116/pexels-photo-2662116.jpeg?auto=compress&cs=tinysrgb&w=800",
  //           "https://images.pexels.com/photos/2387418/pexels-photo-2387418.jpeg?auto=compress&cs=tinysrgb&w=800",
  //           "https://images.pexels.com/photos/147411/italy-mountains-dawn-daybreak-147411.jpeg?auto=compress&cs=tinysrgb&w=800"],
  //         text: '',
  //         position: 2
  //       },
  //       {
  //         name: "sticker",
  //         files: ["https://em-content.zobj.net/thumbs/120/apple/325/man-surfing_1f3c4-200d-2642-fe0f.png",
  //           "https://em-content.zobj.net/thumbs/120/google/350/man-surfing_1f3c4-200d-2642-fe0f.png",
  //           "https://em-content.zobj.net/thumbs/120/microsoft/319/man-surfing_1f3c4-200d-2642-fe0f.png"]
  //       }
  //     ]},
  //       data:{}
  //   },
  //   {
  //     label: "formes",
  //     value:{
  //       layers:[
  //         {name:'label',files:'',text:'NFT #1|NFT #2|NFT #3|NFT #4|NFT #5|NFT #6|NFT #7|NFT #8|NFT #9',position:3},
  //         {name:'triangles',files:'$appli$/assets/triangle1.png,$appli$/assets/triangle2.png,$appli$/assets/triangle3.png',text:'',position:2},
  //         {name:'cercles',files:'$appli$/assets/circle1.png,$appli$/assets/circle2.png,$appli$/assets/circle3.png,$appli$/assets/circle4.png,$appli$/assets/circle5.png',text:'',position:1},
  //         {name:'carrés',files:'$appli$/assets/square1.png,$appli$/assets/square2.png,$appli$/assets/square3.png,$appli$/assets/square4.png,$appli$/assets/square5.png',text:'',position:0},
  //       ],
  //       data:{
  //         title:'UnExemple__idx__',
  //         description:'Ceci est un exemple de data pour NFT',
  //         symbol:'Sample__idx__',
  //         properties:'formes=carré,cercle,triangle\nlabel=NFT',
  //         collection:'SampleCollection',
  //         family:'SampleFamily'
  //       }}
  //   }
  // ]

  sel_platform: string="nftstorage";

  sel_config: Configuration | null=null;
  fontfiles: any[]=[];
  filename_format: string ="image";

  message="";
  palette: any={};
  quality: number=95;
  stockage_available:any={};    //Stockage des documents attachés

  constructor(
      public network:NetworkService,
      public dialog:MatDialog,
      public router:Router,
      public device:DeviceService,
      public operation:OperationService,
      public routes:ActivatedRoute,
      public user:UserService,
      public toast:MatSnackBar,
      public safe:SafePipe,
      public _location:Location,
      public clipboard:Clipboard
  ) {

  }

  ngOnDestroy(): void {
    this.save_config(false);
  }

  total_picture() : number {
    let rc=0
    if(this.sel_config){
      for(let l of this.sel_config?.layers){
        rc=rc+l.elements.length;
      }
    }
    return rc
  }

  eval_max_nft(){
    if(this.sel_config && this.sel_config.layers.length>0) {
      let rc = 1;
      for (let l of this.sel_config.layers) {
        if (!l.unique && l.indexed && l.elements.length > 0) rc = rc * l.elements.length;
      }
      for (let l of this.sel_config.layers) {
        if (l.unique && rc > l.elements.length) rc = l.elements.length;
      }
      this.max_nft = rc;
      if(this.sel_config.limit>this.max_nft)this.sel_config.limit=this.max_nft;
    }
  }


  refresh(){
    if(this.fontfiles.length>0){
      if(this.sel_config && this.sel_config.text && !this.sel_config!.text.font)this.sel_config!.text.font=this.fontfiles[0];
    } else {
      this.network.list_installed_fonts().subscribe((r:any)=>{
        if(r && r.fonts.length>0){
          this.fontfiles=r.fonts;
          this.refresh();
        }
      })
    }
  }


  ngOnInit(): void {
    this.network.get_palettes().subscribe((p)=>{
      this.palette_names=Object.keys(p);
      this.palette=p;
      this.sel_palette=this.palette_names[0];
    })

    getParams(this.routes).then((params:any)=>{
      if(params.title_form)this.title_form=params.title_form;
      this.claim=params.claim || environment.claim || "";
      this.sel_platform=this.network.stockage_available[0];
      this.stockage_available=this.network.stockage_available || params.stockage || "infura";

      for(let i=0;i<this.stockage_available.length;i++){
        let s=this.stockage_available[i];
        if(typeof s=="string"){
          this.stockage_available[i]={label:s.split("-")[0],value:s}
        }
      }

      this.network.list_config().subscribe((r:any)=> {
        if(r){
          this.configs = r.map((x:any)=>{return x.doc});
          let item=localStorage.getItem("config");
          if(item){
            $$("Chargement de la configuration du localStorage")
            this.sel_config=parse(item);
            this.eval_max_nft();
          }else{
            $$("Initialisation d'une nouvelle configuration")
            this.new_conf("localConfig",true);
          }
        }
      },(err)=>{showError(this,err)});


      this.eval_max_nft();
      this.refresh();

    })

  }


  find_config(id:string,field="id"){
    if(this.configs){
      for(let config of this.configs){
        if((field=="id" && config.id==id) || (field=="name" && config.label==id))return config;
      }
    }
    return null;
  }



  getContent(file: File) {
    let rc=file;
    //return rc.split("base64,")[1];
  }


  paiement(nTokenToMint:number,profil:any) {
    return new Promise((resolve, reject) => {
      if(profil.perms.indexOf("free_build")>-1 || profil.perms.indexOf("*")>-1){
        resolve("ok")
      } else {
        // this.user.wallet.sendTransaction(TOKEN_FACTORY_WALLET, nTokenToMint * PRICE_PER_TOKEN).then((result) => {
        //   showMessage(this, "Paiement ok");
        //   resolve(result);
        // }).catch(()=>{reject();})
      }

    });
  }




  add_layer(name="",force=false) {
    if(this.sel_config){
      let names=this.sel_config.layers.map((x)=>{return(x.name)});

      if(name.length == 0)name="layer"+this.sel_config!.layers.length;
      if(names.indexOf(name)>-1)name=name+"_"+now().toString();


      let new_layer={
        params:{},
        name:name,
        elements:[],
        text:"",
        unique:false,
        width:this.sel_config.width,
        height:this.sel_config.height,
        indexed:true,
        position:this.sel_config!.layers.length,
        translation: "0,0",
        scale: "1,1",
        margin: "0,0"
      }


      if(force){
        this.sel_config!.layers.push(new_layer)
        this.save_config();
      } else {
        _prompt(this,"Nom du calque ?",name,"","text","Valider","Annuler",false).then((name:string)=> {
          new_layer.name = name;
          if(names.indexOf(name)==-1){
            this.sel_config!.layers.push(new_layer)
          }else{
            showMessage(this,"Ce nom existe déjà dans les calques");
          }
          this.save_config();
        });
      }
    }

  }


  fill_layer(i:number,w:number,h:number,preview:number){
    return new Promise((resolve,reject) => {
      if(this.sel_config){
        wait_message(this,"Composition de " + i + " calques sur " + this.sel_config!.layers.length)
        this.network.add_layer(this.sel_config!.layers[i],w,h,preview).subscribe(async ()=> {
          wait_message(this);
          i = i + 1;
          if(this.sel_config && i<this.sel_config!.layers.length){
            await this.fill_layer(i,w,h,preview);
          }else{
            resolve(true);
          }
        },(err)=>{showError(this,err)});
      }
    });
  }


  async ask_email_for_collection(){
    let email=await _prompt(this,"Email de reception de la collection",this.user.profil.email,
        "Vous recevrez le lien de téléchargement dés que la collection est disponible","text","Démarrer","Annuler",false);
    this.generate_collection("zip_"+email);
  }

  async ask_confirmation_for_big_collection(format="zip"){
    let conf="no";
    if(this.sel_config!.limit>20){
      conf=await _prompt(this,"Etes-vous sûr de lancer une génération en temps réel ?","","La génération de cette collection risque de prendre beaucoup de temps.");
    }
    if(this.sel_config!.limit<=20 || conf=="yes"){
      this.generate_collection(format);
    }
  }

  preview(limit:number=0,size:string="",delay=500){
    this.previews=[]
    if(size.length==0)size=this.sel_config?.width+"x"+this.sel_config?.height;
    if(limit==0)limit=this.sel_config?.limit || 1;
    this.show_preview=true;
    this.show_conception=false;
    this.message_preview="Preview en cours de construction";
    setTimeout(()=>{
      this.network.get_sequence(this.sel_config!.layers,limit).subscribe((result:any)=>{
        $$("Preview base sur la sequence ",result.sequences)
        let real_limit=Math.min(limit,result.sequences.length);
        for(let i=0;i<real_limit;i++){
          setTimeout(()=>{
            let seq=result.sequences[i];
            this.network.get_composition(seq,this.sel_config!.layers,this.sel_config?.data,size,"base64").subscribe((result:any)=>{
              $$("Récupération de "+result.images[0].substring(0,20)+"...")
              this.add_to_preview([result.images[0]],[result.urls[0]])

              if(this.previews.length==real_limit){
                this.message_preview="";
                this.show_generate=true;
              }
            })
          },i*delay);
        }
      },(err)=>{showError(this,err)});
    },100)

  }

  check_data() : boolean {
    //Vérification du format des datas
    if(this.sel_config!.data.properties && this.sel_config!.data.properties!=""){
      for(let line of this.sel_config!.data.properties.split("\n")){
        if(line.split("=").length!=2){
          showMessage(this,"Format des propriétés/attributs incorrect. La syntaxe doit être attribut=valeur pour chaque ligne");
          return false;
        }
      }
    }

    if(this.sel_config && this.sel_config.data){
      this.sel_config!.data.sequence=this.sel_config?.text.text_to_add.split("|");
      if(this.operation!.sel_ope && this.operation!.sel_ope!.nftlive){
        this.sel_config!.data.operation=this.operation.sel_ope?.id;
      }
    }

    return true;
  }


  generate_collection(format="files base64",delay=500) {
    //Format peut contenir "preview"
    if(!this.sel_config)return;
    this.url_collection="";
    this.save_config(false);
    if(!this.check_data())return;

    this.show_preview=true;
    this.message_preview="Séquençage de la série"

    this.network.get_sequence(this.sel_config.layers,this.sel_config.limit).subscribe(async (result:any)=>{
      let sequences=result.sequences;
      this.message_preview="Avancement 0%";
      let rep:any="ok";
      if(true || sequences.length>environment.visual_cost.quota && this.sel_config?.width!+this.sel_config?.height!>300){
        let nb_tokens_to_generate=sequences.length;
        rep=await _ask_for_paiement(this,this.user.merchant.wallet!.token,
            nb_tokens_to_generate*(environment.visual_cost.price_in_fiat),
            nb_tokens_to_generate*(environment.visual_cost.price_in_crypto),
            this.user.merchant!,
            this.user.wallet_provider,
            "Confirmer la génération des visuels",
            "",
            "",
            this.user.profil.email,
            {contact: "contact@nfluent.io", description: "Génération de "+nb_tokens_to_generate+" visuels", subject: ""},
            this.user.buy_method)
      }

      if(rep){
        this.user.init_wallet_provider(rep.provider,rep.address)
        this.user.nfts_to_mint=[];
        let step=Math.max(sequences.length/10,3);

        this.previews=[];
        this.message_preview="Avancement "+Number(100*step/sequences.length)+"%";

        $$("Démarage du traitement")
        for(let i=0;i<sequences.length;i=i+step){
          setTimeout(()=>{
            let seq=sequences.slice(i,i+step);

            this.network.get_composition(
                seq,
                this.sel_config?.layers!,
                this.sel_config!.data,
                this.sel_config?.width+"x"+this.sel_config?.height,
                format).subscribe((result:any)=>{

              this.add_to_preview(result.urls,result.urls);

              if(this.previews.length==sequences.length){
                this.message_preview="";
                if(format.indexOf("mint")>-1)this.router.navigate(["mint"])
                if(format.indexOf("zip")>-1){
                  this.network.create_zip(result.files,this.user.profil.email).subscribe((result:any)=>{
                    if(!this.user.profil.email){
                     open(result.zipfile,"visuels")
                    }else{
                      showMessage(this, "Travail en cours ... consulter votre boite mail pour retrouver votre collection de visuels")
                    }
                  })
                }
              }else{
                this.message_preview="Avancement "+Math.round(Number(100*i/sequences.length))+"%";
              }

              if(format.indexOf("mint")>-1){
                for(let image of result.urls)
                  if(this.sel_platform && this.sel_platform.length>0 && !this.sel_platform.startsWith("server")){
                    this.network.upload(image,this.sel_platform,"image/webp").subscribe((result:any)=>{
                      this.user.nfts_to_mint.push({file:result.url,filename:result.url,type:"image/webp"})
                    })
                  } else {
                    this.user.nfts_to_mint.push({file:image,filename:image,type:"image/webp"})
                  }
              }


            })
          },i*delay);
        }
      } else {
        this.message_preview="";
        showMessage(this,"Annulation du paiement");
      }


      // this.network.reset_collection().subscribe(async ()=>{
      //
      //   await this.fill_layer(i,this.sel_config?.width || 800,this.sel_config?.height || 800,0);
      //
        // let url=this.network.get_url_collection(
        //     Math.min(this.sel_config!.limit,format=="preview" ? 10 : 1000),
        //     this.filename_format,this.sel_ext.value,
        //     this.sel_config!.width+","+this.sel_config!.height,
        //     this.sel_config!.seed,
        //     this.quality,format,
        //     this.sel_config!.data,
        //     this.sel_config!.data.properties,
        //     this.sel_platform);
        //
        // this.url_collection=url.replace("format=preview","format=zip");

        //
        // }else{
        //   wait_message(this,"Fabrication: Fusion des calques ...",true,2000000);
        //   this.network._get(url,"",timeout).subscribe((r: any) => {
        //         showMessage(this, "Télécharger sur le lien pour démarrer la fabrication et le téléchargement de la collection")
        //         //    = this.network.server_nfluent + "/api/images/" + r.archive + "?f=" + r.archive;
        //         $$("Lien de téléchargement " + this.url_collection);
        //
        //         if (direct_mint) {
        //           wait_message(this)
        //           showMessage(this, "L'ensemble des liens vers les images est disponibles dans votre presse-papier")
        //           this.user.nfts_to_mint = r.preview;
        //           this.router.navigate(["mint"]); //A priori les paramétres ont été intégré au lancement
        //           // this.router.navigate(["mint"],{queryParams:{param:setParams({
        //           //       toolbar: this.user.toolbar_visible,
        //           //       networks: this.networks_available,
        //           //       stockage: this.stockage_available
        //           //     })}});
        //         } else {
        //           wait_message("Préparation de l'aperçu")
        //           setTimeout(()=>{
        //             this.previews = r.preview;
        //             this.show_generate = false;
        //             this.show_preview = true;
        //             this.show_conception = false;
        //             wait_message(this)
        //           },50);
        //         }
        //       }
        //       , (err) => {
        //         showError(this, err);
        //       })
      //   }
      //
      // });

    })
  }

  attributes(arg0: number, filename_format: string, value: string, arg3: string, seed: number, quality: number | undefined, format: string, data: { title: string; symbol: string; description: string; properties: string; files: string; operation: string | undefined; tags: string; sequence: string[] | undefined; }, attributes: any) {
    throw new Error('Method not implemented.');
  }


  //Génére un sticker sur la base d'un texte et l'ajoute à la layer l
  generate(l:Layer){
    if(this.sel_config){
      l.params={
        text:this.sel_config.text.text_to_add,
        x:this.sel_config.text.position_text.x,
        y:this.sel_config.text.position_text.y,
        font:{
          name:this.fontfiles,
          size:this.sel_config.text.fontsize,
          color:this.sel_config.text.color
        }
      }
      if(l==null){
        showMessage(this,"Vous devez sélectionner la couche cible pour créer le visuel");
        return;
      }

      let i=0;
      for(let txt of this.sel_config.text.text_to_add.split("|")){
        if(txt.length>0){
          if(i==this.sel_colors.length)i=0;
          let elt=this.create_element(txt);
          if(this.usePalette)elt.fontstyle.color=this.sel_colors[i];
          l.elements.push({"text":elt});
          i=i+1;
        }
      }

      this.message="Génération de la série d'images";
      this.network.update_layer(l,20).subscribe((r:any)=>{
        this.message="";
        l.elements=r.elements;
      },(err)=>{showError(this,err);});
    }

  }


  onclick_on_text($event: MouseEvent,l:Layer) {
    this.sel_config!.text.position_text={x:$event.offsetX/2,y:$event.offsetY/2}
  }



  modify_element($event:MouseEvent, layer: Layer, element:any) {
    let pos=layer.elements.indexOf(element);
    if($event.button==0){
      $event.stopPropagation();
      if($event.ctrlKey){
        layer.elements.splice(pos,1);
        this.eval_max_nft();
      }

      if($event.altKey){
        this.network.wait("Traitement de suppression du fond en cours");
        this.network.remove_background(element).subscribe((result:any)=>{
          this.network.wait("")
          element.image=result["image"];
          layer.elements[pos]=element;
          this.eval_max_nft();
        },()=>{this.network.wait("");})
      }

      // if($event.altKey){
      //   let index=this.sel_config!.layers.indexOf(layer);
      //   if(index==this.sel_config!.layers.length-1)index=-1;
      //   let new_layer=this.sel_config!.layers[index+1];
      //   new_layer.elements.push(element);
      //   layer.elements.splice(pos,1);
      // }

      if($event.shiftKey){
        if(pos==0)pos=1;
        let e=layer.elements[pos-1];
        layer.elements[pos-1]=layer.elements[pos];
        layer.elements[pos]=e;
        this.eval_max_nft();
      }

      this.save_config();

      // this.network.update_layer(layer).subscribe((elements:any)=>{
      //   showMessage(this,"Mise a jour");
      // });
    }
  }




  update_position(layer: Layer, variation:number) {
    let idx=this.sel_config!.layers.indexOf(layer);
    if(layer.position+variation>=0 && layer.position<=this.sel_config!.layers.length){
      this.sel_config!.layers[idx+variation].position=this.sel_config!.layers[idx+variation].position-variation
      layer.position=layer.position+variation;
      this.sort_layers();
    }
  }



  delete_layer(layer: Layer) {
    let pos=this.sel_config!.layers.indexOf(layer);
    this.sel_config!.layers.splice(pos,1);
    this.eval_max_nft();
  }



  add_link(layer:Layer) {
    this.dialog.open(PromptComponent, {
      width: 'auto', data:
          {
            title: "Liste des liens",
            type: "text",
            onlyConfirm: false,
            lbl_ok: "Ok",
            lbl_cancel: "Annuler"
          }
    }).afterClosed().subscribe((urls: string) => {
      if (urls) {
        for(let url of urls.split(",")){
          layer.elements.push({image:url});
        }
      }
    });
  }


  build_sample(layers:any[],data:any={},reset=true):boolean {
    if(layers && layers.length==0)return false;

    _prompt(this,"Remplacer la configuration actuelle","","","boolean").then(()=>{
      if(reset)this.sel_config!.layers=[];

      for(let l of layers){
        $$("Mise a jour des noms de fichier avec le chemin complet");
        for(let k=0;k<100;k++)l["files"]=l["files"].replace("$appli$",environment.appli);

        let layer:Layer={
          params:{},
          name:l.hasOwnProperty("name") ? l.name : "layer",
          elements:[],
          text:l["text"],
          unique:false,
          indexed:true,
          position:l.position,
          margin:"0"
        }

        if(l["text"]){
          for(let text of l["text"].split("|")){
            layer.elements.push({text:this.create_element(text)})
          }
        } else {
          if(l["files"] && l["files"].length>0)
            for(let file of l["files"].split(",")){
              layer.elements.push({image:file});
            }
        }

        this.network.update_layer(layer).subscribe((r:any)=>{
          layer.elements=r.elements;
          this.sel_config!.layers.push(layer);
          if(this.sel_config!.layers.length==layers.length)this.sort_layers();
        });
        this.sel_config!.data=data;
      }
    })
    return true;
  }


  sort_layers(){
    this.sel_config!.layers.sort((l1,l2) => {if(l1.position>l2.position)return 1; else return -1;})
  }



  find_font(filename:string) {
    if(this.fontfiles){
      for(let f of this.fontfiles){
        if(f.file==filename)
          return f;
      }
    }
    return null;
  }


  update_config(sel_config:Configuration | null,no_prompt=false) {
    //tag: load_config
    // let rep=await _prompt(this,"Charger une nouvelle configuration","",
    //     "Remplacer votre configuration actuelle ?","oui/non",
    //     "Remplacer","Annuler",true, [],no_prompt);
    // if(rep=="yes"){
    this.sel_config=sel_config;
    if(this.sel_config){
      localStorage.setItem("config",stringify(sel_config))

      // this.sel_platform = this.sel_config.platform;
      // if(!this.sel_platform || this.sel_platform.value==""){
      //   this.sel_platform=this.network.config["PLATFORMS"][isLocal(environment.appli) ? 4 : 3];
      // }
      //
      // if (this.sel_config.layers) {
      //   for (let l of this.sel_config.layers) {
      //     for (let e of l.elements) {
      //       if (this.sel_platform!.value == "nfluent") e.image = e.image.replace("http://127.0.0.1:4242/", "https://server.nfluent.io:4242/");
      //       if (this.sel_platform!.value == "nfluent local") e.image = e.image.replace("https://server.nfluent.io:4242/", "http://127.0.0.1:4242/");
      //     }
      //   }
      // }
      this.previews = [];

    } else {
      this._location.replaceState("/creator");
    }
    this.eval_max_nft();
  }

  check_config(config:any){
    for (let l of this.sel_config!.layers) {
      if (l.elements) {
        for (let f of l.elements)
          f = "\"" + f + "\""
      } else {
        return false;
      }
    }
    return true;
  }

  //https://server.f80lab.com/api/configs/?format=file
  config_with_image=true;

  save_config(with_file=false) : Promise<string> {
    return new Promise((resolve,reject) => {
      localStorage.setItem("config",stringify(this.sel_config))

      if(with_file){
        let body={
          "filename":"config.yaml",
          "content":stringify(this.sel_config),
          "type":"application/json"
        }
        this.network.upload(body,"server").subscribe((r:any)=>{
          //this.network.server_nfluent + "/api/configs/" + this.sel_config!.id + "/?format=file"
          open(r.url, "config");
        })

      }
    });
  }


  isValide(conf:Configuration){
    if(!conf.layers || conf.layers.length==0)return false;
    if(!conf.data)return false;
    return true;
  }

  async on_upload_config($event: any) {
    let r=await _prompt(this,"Effacer la configuration actuelle");
    if(r=="yes"){
      let config:Configuration=parse($event.file);
      if(this.isValide(config)){
        this.sel_config=config;
        this.update_config(config);
      }else{
        showMessage(this,"Cette configuration n'est pas conforme");
      }

    }
  }

  add_serial(layer: Layer) {
    _prompt(this,"Début de la série","1","","number","ok","Annuler",false).then((txtStart:string)=>{
      _prompt(this,"Fin de la série","100","","number","ok","Annuler",false).then((txtEnd:string)=> {
        let modele=this.sel_config!.text.text_to_add;
        if(modele.indexOf("__idx__")==-1)modele=modele+"__idx__";
        this.sel_config!.text.text_to_add="";
        let nbr_digits=txtEnd.length;
        for(let i=Number(txtStart);i<=Number(txtEnd);i++){
          this.sel_config!.text.text_to_add=this.sel_config!.text.text_to_add+modele.replace("__idx__",i.toString().padStart(nbr_digits,'0'))+"|";
        }
        this.save_config();
      });
    })
  }



  clear_layer(layer: Layer) {
    for(let f of layer.elements){
      if(f.image.indexOf("/api/images/")>-1){
        let id=f.image.split("/api/images/")[1].split("?")[0];
        //this.network.remove_image(id).subscribe(()=>{});
      }
    }
    layer.elements=[];
    this.save_config();
    this.eval_max_nft();
  }


  open_file(file: any) {
    let data=file.image;
    if(data.startsWith("data:")){
      let w = window.open('about:blank');
      let image = new Image();
      image.src = data;
      setTimeout(()=>{if(w)w.document.write(image.outerHTML);}, 0);
    } else {
      open(data,"preview");
    }
  }

  create_element(text: any,name="") {
    return {
      name:name,
      text:text,
      fontstyle: {
        name: this.sel_config!.text.font.file,
        color: this.sel_config!.text.color,
        size: this.sel_config!.text.fontsize
      },
      dimension:[this.sel_config!.width, this.sel_config!.height],
      x: Number(this.sel_config!.text.position_text.x),
      y: Number(this.sel_config!.text.position_text.y),
    }
  }

  generate_with_color(layer: Layer) {
    this.network.clone_with_color(layer,this.sel_config!.text.color,this.sel_palette).subscribe((images:any)=>{
      for(let img of images){
        layer.elements.push({image:img});
      }
    })
  }

  change_palette($event: MatSelectChange) {
    this.sel_colors=Object.values(this.sel_palette);
  }



  load_text_config(l:Layer) {
    if(l.params){
      this.fontfiles=l.params.font.name;
      this.sel_config!.text.position_text.x=l.params.x;
      this.sel_config!.text.position_text.y=l.params.y;
      this.sel_config!.text.text_to_add=l.params.text;
      this.sel_config!.text.color=l.params.font.color;
      this.sel_config!.text.fontsize=l.params.font.size;
    }
  }


  create_location_from_name(name:string):string {
    if(name.length>50)name=hashCode(name).toString(16);
    return name.replace(" ","").substring(0,50)+".yaml";
  }



  new_conf(new_name:string,no_prompt=false){
    //Génération d'une nouvelle config
    //#tag new_config newConfig
    this.update_config({
      quality: 98,
      version: 1,
      message:"",
      id: now("hex").toString(),
      height: 800,
      width: 800,
      data: {
        description: "",
        files: "",
        operation: "",
        properties: "",
        symbol: "token__idx__",
        title: "MonNFT",
        tags:"",
        sequence:[],
        creators:""
      },
      attributes: {},
      layers: [],
      limit: 10,
      help:"",
      max_items: 11,
      label: new_name,
      platform: {label: "", value: ""},
      seed: 0,
      text: {color: "#FFFFFF", fontsize: 12, position_text: {x: 10, y: 10}, text_to_add: "Texte ici",font:{name:"Corbel",file:"corbel.ttf"}},
      location: this.create_location_from_name(new_name)
    },no_prompt)

    this.add_layer("fond",true);
    this.add_layer("text_logo",true);
  }



  async reset() {
    let r="yes";
    let default_name="maconfig";
    if(this.sel_config){
      default_name=this.sel_config.label+"_v2";
      r=await _prompt(this,"Effacer la configuration actuelle ?","","","","ok","annuler",true);
    }
    if(r=="yes"){
      if(this.user.isConnected()){
        let name=await _prompt(this,"Nom de la configuration",default_name,"","text","Commencer","Annuler",false);
        if(!this.find_config(name,"name")){
          this.new_conf(name);
          this.configs.push(this.sel_config!);
        } else {
          showMessage(this,"Ce nom existe déjà");
        }
      } else {
        this.new_conf("locale_config");
      }
    }
  }

  upload_image_in_correct_order(idx=0,l_images:string[],layer:Layer) : Promise<Layer>{
    return new Promise((resolve) => {
      let img = l_images[idx];
      this.network.upload(img, this.sel_platform, "image/svg").subscribe((r: any) => {
        layer.elements.push({"image": r.url, type: "image/svg","name":"svg_"+layer.name+"_"+idx});
        if (l_images.length == idx + 1) {
          resolve(layer)
        } else {
          this.upload_image_in_correct_order(idx + 1, l_images, layer)
        }
      })
    })
  }


  async find_image() {
    showMessage(this,"Il est possible de faire directement glisser les images d'un site web vers le calque souhaité")
    let resp=await _prompt(this,"Saisissez un mot clé (de préférence en anglais)",
        "rabbit",
        "Accéder directement à plusieurs moteurs de recherche d'image","text",
        "Rechercher","Annuler",false)
    open("https://www.google.com/search?q=google%20image%20"+resp+"&tbm=isch&tbs=ic:trans","search_google");
    open("https://giphy.com/search/"+resp,"giphy")
    open("https://pixabay.com/fr/vectors/search/"+resp+"/","search_vector")
    open("https://thenounproject.com/search/icons/?iconspage=1&q="+resp,"search_vector")
    open("https://pixabay.com/images/search/"+resp+"/?colors=transparent","search_transparent")
    open("https://www.pexels.com/fr-fr/chercher/"+resp+"/","search_pexels")
  }

  //add_image_to_layer ajouter une image
  //tag upload_file
  title_form="Générateur de visuels NFTs";
  claim="";
  show_preview:boolean=false;
  show_conception: boolean=true;
  on_upload(evt: any,layer:Layer) {

    let body={
      filename:evt.filename,
      "content":evt.file,
      "type":evt.type
    }

    if(body.filename.endsWith("svg")){
      this.network.generate_svg(evt.file,this.sel_config!.text.text_to_add,layer.name).subscribe(async (r:any)=>{
        layer=await this.upload_image_in_correct_order(0,r,layer)
        this.eval_max_nft();
      })
    }else{
      this.message="Chargement des visuels";
      this.network.upload(body,this.sel_platform,"image/png","webp").subscribe((r:any)=>{
        this.message="";
        layer.elements.push({image:r.url,name:normalize(evt.filename)});
        this.eval_max_nft();
        this.save_config();
      },(err:any)=>{
        showError(this,err);
      })
    }
  }

  file_treatment(blob:any,layer:Layer){
    let reader = new FileReader();
    reader.onload=()=>{
      let body={filename:blob.name,file:reader.result,type:blob.type};
      this.on_upload(body,layer);
    }
    reader.readAsDataURL(blob)
  }


  paste_picture(layer: Layer) {
    navigator.clipboard.read().then((content)=>{
      for (const item of content) {
        if (!item.types.includes('image/png')) {
          showMessage(this,"Ce contenu ne peut être intégré. Enregistrez l'image sur votre ordinateur et importez là ensuite");
        }
        item.getType('image/png').then((blob:Blob)=>{
          this.file_treatment(blob,layer);
        });
      }
      this.save_config();
    })
  }

  async del_config(sel_config: any) {
    this.network.del_config(sel_config.id).subscribe(async () => {
      showMessage(this, "Configuration supprimé");
      this.eval_max_nft();
      this.update_config(null);
    })
  }

  apply_filter(layer: Layer) {
    let filters=[
      {label:"Noicir",value:"to_black"},
      {label:"Eclaircir",value:"to_white"},
      {label:"Posteriser",value:"posterize"},
      {label:"Solariser",value:"solarize"},
      {label:"Flouter",value:"blur"},
      {label:"Equaliser",value:"equalize"},
      {label:"Noir & blanc",value:"grayscale"},
      {label:"Retourner",value:"flip"},
      {label:"Mirroir",value:"mirror"},
      {label:"Contraster",value:"contrast"}
    ]
    _prompt(this,"Choisir un filtre","","","list","ok","Annuler",false,filters).then((filter:any)=>{
      this.network.add_layer(layer,this.sel_config!.width,this.sel_config!.height).subscribe(()=> {
        this.network.apply_filter(layer.name,filter).subscribe((r:any)=>{
          for(let i of r.images)
            layer.elements.push({image:i})
          this.refresh();
        })
      });
    })
  }


  miner() {
    this.router.navigate(["miner"],{queryParams:{param:setParams({files:this.upload_files},"","")}})
  }



  async transform(layer: Layer) {
    //if(!layer.translation)layer.translation="0,0"
    //if(!layer.scale)layer.scale="1,1";
    if(!layer.margin)layer.margin="0";
    //layer.translation=await _prompt(this,"Translation (x,y) ?",layer.translation)
    //layer.scale=await _prompt(this,"Echelle (x,y) ?",layer.scale)
    layer.margin=await _prompt(this,"Largeur du cadre ?",layer.margin,"Largeur en pixel sur horizontal,vertical ou juste la largeur")
    if(!layer.margin)layer.margin="0,0"
    if(layer.margin.indexOf(",")==-1)layer.margin=layer.margin+","+layer.margin;
  }

  async on_upload_attributs($event: any) {
    //await this.fill_layer(0,200,200,0);
    this.network.upload_attributes(this.sel_config!.label,$event.file.split("base64,")[1]).subscribe((resp:any)=>{
      showMessage(this,"Fichier d'attributs associés")
      this.save_config();
    });
  }


  clear_data() {
    _prompt(this,"Effacer l'ensemble des propriétés","","","","Effacer","Annuler",true).then(()=>{
      this.sel_config!.data = {
        operation: this.operation.sel_ope?.id,
        tags: "",
        title: "",
        creators:this.user.addr ? (this.user.addr+":100%") : "",
        symbol: "",
        description: "",
        sequence:[],
        properties: "",
        files: ""
      }
    })
  }

  // async online_config() {
  //   let url=await _prompt(this,"Lien url de votre config","https://");
  //   this.network.getyaml(url).subscribe((config:any)=>{
  //     this.configs.push(config);
  //     this.sel_config=config;
  //   });
  // }

  // async clone() {
  //   let new_name=await _prompt(this,"Nouveau nom",this.sel_config?.name+"_clone");
  //   this.sel_config=JSON.parse(JSON.stringify(this.sel_config));
  //   this.sel_config!.name=new_name;
  //   this.sel_config!.id=now("hex").toString();
  //   this.configs.push(this.sel_config!);
  // }
  show_generate=false;

  drop(layer: Layer, $event: any) {
    for(let file of $event){
      this.file_treatment(file,layer);
    }
  }

  search_images(layer: Layer) {
    let pos=this.sel_config?.layers.indexOf(layer) || 0;
    let sample=(pos==0 ? "background" : "emoji");
    _prompt(this,"Recherche d'images",sample,
        "Votre requête en quelques mots en ANGLAIS de préférence (ajouter 'sticker' pour des images transparentes)",
        "text",
        "Rechercher",
        "Annuler",false).then((query:string)=>{
      if(pos>0 && query.indexOf("sticker")==-1){query=query+" sticker"};
      this.network.search_images(query,(layer.position>0)).subscribe((r:any)=>{
        _prompt(this,"Choisissez une ou plusieurs images","","","images","Sélectionner","Annuler",false,r.images).then((images:string)=>{
          let idx=0
          for(let link of images){
            layer.elements.push({image:link,name:"bank_"+now("rand")+"_"+idx,ext:"image/jpg"});
            idx=idx+1
          }
          this.save_config();
          this.eval_max_nft()
        })
      })
    })

  }

  edit_name(layer: Layer) {
    _prompt(this,"Changer le nom de la couche",layer.name,"","text","Enregistrer","Annuler",false).then((new_name:string)=>{
      layer.name=new_name;
    })
  }

  // choose_sample() {
  //   let sample=this.samples[Math.trunc(Math.random()*this.samples.length)].value;
  //   this.build_sample(sample.layers,sample.data,false);
  // }
  w_data_field: string="350px"
  sel_font: any;
  message_preview: string = "";


  publish(platform="nfluent",to_clipboard=true) {
    return new Promise((resolve) => {
      this.network.upload(this.sel_config,platform,"plain/text").subscribe((rc:any)=>{
        if(to_clipboard){
          this.clipboard.copy(rc.url);
          showMessage(this,"Le lien à partager est dans le presse-papier");
        }
        resolve(rc);
      });
    });
  }

  download_collection(format="zip") {
    showMessage(this,"Votre collection est en cours de préparation");
    window.location.assign(this.url_collection);
  }

  show_max_item() {
    this.sel_config!.max_items=(this.sel_config!.max_items<500 ? 500 : 15);
    showMessage(this,"Pour repasser en vue réduite, utiliser de nouveau ce bouton");
  }

  select_file(img: any) {
    let idx=this.previews.indexOf(img);
    img.selected=!img.selected;
    if(img.selected){
      img.style["opacity"]="1.0"
    }else{
      img.style["opacity"]="0.3"
    }
    this.previews[idx]=img;
  }

  add_to_preview(images:any[],urls:any[]) {
    for(let i=0;i<images.length;i++){
      this.previews.push({src:images[i],url:urls[i],selected:true,style:{width: "100px","margin-left":"5px"}});
    }
  }

  save_file(img: any) {
    download_file(img.src,img.filename,"image/webp");
  }
}
