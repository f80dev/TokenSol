import {Component, OnDestroy, OnInit} from '@angular/core';

import {NetworkService} from "../network.service";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {$$, getParams, hashCode, isLocal, normalize, now, setParams, showError, showMessage} from "../../tools";
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


@Component({
  selector: 'app-creator',
  templateUrl: './creator.component.html',
  styleUrls: ['./creator.component.css']
})
//test : http://localhost:4200/creator

export class CreatorComponent implements OnInit,OnDestroy {
  backcolor="black";

  platforms=null;
  webstorage_platform=[{label:"",value:""}]
  sel_webstorage_platform: any;
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

  sel_platform: { label:string,value:string } | undefined;

  sel_config: Configuration | null=null;
  fontfiles: any;
  filename_format: string ="image";

  message="";
  palette: any={};
  quality: number=95;

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
    if(this.fontfiles){
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

      this.platforms=this.network.config["PLATFORMS"];
      this.webstorage_platform=this.network.config["PLATFORMS"];
      if(this.platforms)this.sel_platform=this.platforms[0];
      this.sel_webstorage_platform=this.webstorage_platform[0];

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
        translation: {x:0,y:0},
        scale: {x:1,y:1}
      }


      if(force){
        this.sel_config!.layers.push(new_layer)
        this.save_config();
      } else {
        _prompt(this,"Nom du calque ?",name).then((name:string)=> {
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


  fill_layer(i:number,w:number,h:number,preview:number,func:Function){
    if(this.sel_config){
      this.message="Composition de " + i + " calques sur " + this.sel_config!.layers.length;
      this.network.add_layer(this.sel_config!.layers[i],w,h,preview).subscribe(()=> {
        i = i + 1;
        if(this.sel_config && i<this.sel_config!.layers.length){
          this.fill_layer(i,w,h,preview,func);
        }else{
          func();
        }
      },(err)=>{showError(this,err)});
    }

  }



  generate_collection(format="zip",direct_mint=false) {
    //Format peut contenir "preview"
    if(!this.sel_config)return;
    this.url_collection="";
    this.save_config(false);

    //Vérification du format des datas
    if(this.sel_config!.data.properties && this.sel_config!.data.properties!=""){
      for(let line of this.sel_config!.data.properties.split("\n")){
        if(line.split("=").length!=2){
          showMessage(this,"Format des propriétés/attributs incorrect. La syntaxe doit être attribut=valeur pour chaque ligne");
          return;
        }
      }
    }

    let i=0;

    this.message="";
    this.network.reset_collection().subscribe(()=>{
      this.message="Fabrication: chargement des images ..."
      this.fill_layer(i,this.sel_config?.width || 800,this.sel_config?.height || 800,0,()=>{

        if(this.sel_config && this.sel_config.data){
          this.sel_config!.data.sequence=this.sel_config?.text.text_to_add.split("|");
          if(this.operation!.sel_ope && this.operation!.sel_ope!.nftlive){
            this.sel_config!.data.operation=this.operation.sel_ope?.id;
          }
          if(!this.sel_config.data.creators || this.sel_config.data.creators.length==0)this.sel_config.data.creators=this.user.addr+":100%";
        }


        if(!direct_mint)showMessage(this,"L'aperçu se limite à 10 NFT maximum");

        this.url_collection="";


        // @ts-ignore
        this.message="Fabrication: Fusion des calques ..."
        let url=this.network.get_url_collection(
            Math.min(this.sel_config!.limit,format=="preview" ? 10 : 1000),
            this.filename_format,this.sel_ext.value,
            this.sel_config!.width+","+this.sel_config!.height,
            this.sel_config!.seed,
            this.quality,format,
            this.sel_config!.data,
            this.sel_config!.data.properties,
            this.sel_webstorage_platform.value);
        this.url_collection=url.replace("format=preview","format=zip");

        this.network._get(url,"",200000).subscribe((r: any) => {
              showMessage(this, "Télécharger sur le lien pour démarrer la fabrication et le téléchargement de la collection")
              //    = this.network.server_nfluent + "/api/images/" + r.archive + "?f=" + r.archive;
              $$("Lien de téléchargement " + this.url_collection);

              this.message = "";

              if (direct_mint) {
                showMessage(this, "L'ensemble des liens vers les images est disponibles dans votre presse-papier")
                this.user.nfts_to_mint = this.previews;
                this.router.navigate(["mint"]);
              } else {
                this.previews = r.preview;
                this.show_generate = false;
                this.show_preview = true;
                this.show_conception = false;
              }
            }
        , (err) => {
          showError(this, err);
        })


        // if(format=="upload"){
        //   this.network.wait("");
        //   this.network.get_collection(Math.min(this.sel_config.limit,50),this.filename_format,this.sel_ext,this.sel_config!.width+","+this.sel_config!.height,this.sel_config.seed,this.quality,"upload",this.sel_config!.data,this.sel_platform).subscribe((r:any) => {
        //     this.upload_files=[];
        //     for(let item of r){
        //       // @ts-ignore
        //       this.upload_files.push(item['url']);
        //     }
        //   });
        // }


      });
    },(err)=>{showError(this,err);})
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
      },(err)=>{
        showError(this,err);
      });
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
      }

      if($event.altKey){
        this.network.wait("Traitement de suppression du fond en cours");
        this.network.remove_background(element).subscribe((result:any)=>{
          this.network.wait("")
          element.image=result["image"];
          layer.elements[pos]=element;
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
      }

      this.network.update_layer(layer).subscribe((elements:any)=>{
        showMessage(this,"Mise a jour");
      });
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
          translation:{x:0,y:0},
          scale:{x:1,y:1}
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


  async update_config(sel_config:Configuration | null,no_prompt=false) {
    let rep=await _prompt(this,"Charger une nouvelle configuration","",
        "Remplacer votre configuration actuelle ?","",
        "Remplacer","Annuler",true, [],no_prompt);
    if(rep=="yes"){
      this.sel_config=sel_config;
      if(this.sel_config){
        localStorage.setItem("config",stringify(sel_config))

        this.sel_platform = this.sel_config.platform;
        if(!this.sel_platform || this.sel_platform.value==""){
          this.sel_platform=this.network.config["PLATFORMS"][isLocal(environment.appli) ? 4 : 3];
        }

        if (this.sel_config.layers) {
          for (let l of this.sel_config.layers) {
            for (let e of l.elements) {
              if (this.sel_platform!.value == "nfluent") e.image = e.image.replace("http://127.0.0.1:4242/", "https://server.nfluent.io:4242/");
              if (this.sel_platform!.value == "nfluent local") e.image = e.image.replace("https://server.nfluent.io:4242/", "http://127.0.0.1:4242/");
            }
          }
        }
        this.previews = [];

      } else {
        this._location.replaceState("/creator");
      }
      this.eval_max_nft();
    }
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


  on_upload_config($event: any) {
    let config:Configuration=parse($event.file);
    this.configs.push(config);
    this.update_config(config);
  }

  add_serial(layer: Layer) {
    _prompt(this,"Début de la série","1","","number").then((txtStart:string)=>{
      _prompt(this,"Fin de la série","100","","number").then((txtEnd:string)=> {
        let modele=this.sel_config!.text.text_to_add;
        if(modele.indexOf("_idx_")==-1)modele=modele+"_idx_";
        this.sel_config!.text.text_to_add="";
        let nbr_digits=txtEnd.length;
        for(let i=Number(txtStart);i<=Number(txtEnd);i++){
          this.sel_config!.text.text_to_add=this.sel_config!.text.text_to_add+modele.replace("_idx_",i.toString().padStart(nbr_digits,'0'))+"|";
        }
        this.save_config();
      });
    })
  }



  clear_layer(layer: Layer) {
    for(let f of layer.elements){
      if(f.image.indexOf("/api/images/")>-1){
        let id=f.image.split("/api/images/")[1].split("?")[0];
        this.network.remove_image(id).subscribe(()=>{});
      }
    }
    layer.elements=[];
    this.save_config();
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
    this.update_config({
      quality: 98,
      version: 1,
      message:"",
      id: now("hex").toString(),
      height: 800,
      width: 800,
      data: { description: "", files: "",
        operation: "", properties: "",
        symbol: "token__idx__", title: "",
        tags:"",sequence:[],
        creators:this.user.addr+":100%"},
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
        let name=await _prompt(this,"Nom de la configuration",default_name);
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



  async find_image() {
    let resp=await _prompt(this,"Saisissez un mot clé (de préférence en anglais)")
    open("https://www.google.com/search?q=google%20image%20"+resp+"&tbm=isch&tbs=ic:trans","search_google");
    open("https://giphy.com/search/"+resp,"giphy")
    open("https://pixabay.com/fr/vectors/search/"+resp+"/","search_vector")
    open("https://thenounproject.com/search/icons/?iconspage=1&q="+resp,"search_vector")
    open("https://pixabay.com/images/search/"+resp+"/?colors=transparent","search_transparent")
    open("https://www.pexels.com/fr-fr/chercher/"+resp+"/","search_pexels")
    open(""+resp+"/","search_pexels")
  }


  //add_image_to_layer ajouter une image
  //tag upload_file
  title_form="Générateur de visuels NFTs";
  show_preview:boolean=false;
  show_conception: boolean=true;
  on_upload(evt: any,layer:Layer) {

    let body={
      filename:evt.filename,
      "content":evt.file,
      "type":evt.type
    }

    if(body.filename.endsWith("svg")){
      this.network.generate_svg(evt.file,this.sel_config!.text.text_to_add,layer.name).subscribe((r:any)=>{
        for(let img of r){
          this.network.upload(img,this.sel_platform!.value,"image/svg").subscribe((r:any)=>{
            layer.elements.push({"image":r.url,type:"image/svg"});
          })
        }
        this.eval_max_nft();
      })
    }else{
      this.message="Chargement des visuels";
      this.network.upload(body,this.sel_platform!.value,"image/png","webp").subscribe((r:any)=>{
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
    this.router.navigate(["miner"],{queryParams:{param:setParams({files:this.upload_files})}})
  }




  transform(layer: Layer) {
    if(!layer.translation)layer.translation={x:0,y:0};
    if(!layer.scale)layer.scale={x:1,y:1};

    _prompt(this,"Translation (x,y) ?",layer.translation.x+","+layer.translation.y).then((translation:any)=>{
      layer.translation.x=Number(translation.split(",")[0]);
      layer.translation.y=Number(translation.split(",")[1]);

      _prompt(this,"Echelle (x,y) ?",layer.scale.x+","+layer.scale.y).then((scale:any)=> {
        layer.scale.x = Number(scale.split(",")[0]);
        layer.scale.y = Number(scale.split(",")[1]);
      });
    })
  }



  on_upload_attributs($event: any) {
    this.fill_layer(0,200,200,0,()=>{
      this.network.upload_attributes(this.sel_config!.label,$event.file.split("base64,")[1]).subscribe((resp:any)=>{
        showMessage(this,"Fichier d'attributs associés")
        this.save_config();
      })
    });
  }


  clear_data() {
    _prompt(this,"Effacer l'ensemble des propriétés","","","","Effacer","Annuler",true).then(()=>{
      this.sel_config!.data = {
        operation: this.operation.sel_ope?.id,
        tags: "",
        title: "",
        creators:this.user.addr+":100%",
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
    _prompt(this,"Recherche d'images","background","Votre requête en quelques mots (ANGLAIS de préférence)","text","Rechercher","Annuler").then((query:string)=>{
      this.network.search_images(query,(layer.position>0)).subscribe((r:any)=>{
        _prompt(this,"Choisissez une ou plusieurs images","","","images","Sélectionner","Annuler",false,r.images).then((images:string)=>{
          for(let link of images){
            layer.elements.push({image:link});
          }
          this.save_config();
        })
      })
    })

  }

  edit_name(layer: Layer) {
    _prompt(this,"Changer le nom de la couche",layer.name).then((new_name:string)=>{
      layer.name=new_name;
    })
  }

  // choose_sample() {
  //   let sample=this.samples[Math.trunc(Math.random()*this.samples.length)].value;
  //   this.build_sample(sample.layers,sample.data,false);
  // }


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
}
