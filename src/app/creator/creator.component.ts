import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {$$, getParams, normalize, setParams, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PLATFORMS, PRICE_PER_TOKEN, TOKEN_FACTORY_WALLET} from "../../definitions";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from "@angular/common";
import {MatSelectChange} from "@angular/material/select";
import {ClipboardModule} from "@angular/cdk/clipboard";
import {UserService} from "../user.service";
import {Layer} from "../../create";
import {OperationService} from "../operation.service";


@Component({
  selector: 'app-creator',
  templateUrl: './creator.component.html',
  styleUrls: ['./creator.component.css']
})
//test : http://localhost:4200/creator

export class CreatorComponent implements OnInit {
  layers: Layer[]=[];
  col_width=200;
  backcolor="black";
  col_height=200;
  platforms=PLATFORMS;
  limit=10;
  show_addtext:any;
  configs:string[]=[];
  previews:any[]=[];
  sel_ext: string="webp";
  seed: number=0;
  sel_palette: string="purple";
  palette_names: string[]=[];
  usePalette: boolean=false;
  sel_colors: any[]=[];
  upload_files=[];


  text_to_add: string="Texte ici";
  fontsize: number=12;
  color: any="#FFFFFF";

  font:any= {name:"Corbel",file:"corbel.ttf"}
  sel_platform: any="nfluent";
  sel_config: any="";
  fontfiles: any;
  position_text: { x: any; y: any }={x:10,y:10};
  filename_format: string ="image";

  message="";
  max_items: number=8;
  config_name: string="maconfig";
  palette: any={};

  constructor(
    public network:NetworkService,
    public dialog:MatDialog,
    public router:Router,
    public operation:OperationService,
    public routes:ActivatedRoute,
    public user:UserService,
    public toast:MatSnackBar,
    public safe:SafePipe,
    public _location:Location,
    public clipboard:ClipboardModule
  ) {
    this.init_data();
  }


  refresh(){
    this.network.list_installed_fonts().subscribe((r:any)=>{
      this.fontfiles=r.fonts;
      this.font=r.fonts[0];
    })
  }



  load_configs(){
    return new Promise((resolve, reject) => {
      this.network.list_config().subscribe((r:any)=> {
        this.configs = r.files;
        resolve(r.files);
      });
    });
  }



  ngOnInit(): void {
      if(environment.appli.indexOf("127.0.0.1")>-1 || environment.appli.indexOf("localhost")>-1){
        this.sel_platform="nfluent"
      }

      this.layers=[];
      this.network.get_palettes().subscribe((p)=>{
        this.palette_names=Object.keys(p);
        this.palette=p;
        this.sel_palette=this.palette_names[0];
      })
    getParams(this.routes).then((params:any)=>{
      this.load_configs().then(()=>{
        if(this.configs.length>0){
          this.sel_config=params["config"];
          if(this.sel_config)this.load_config(this.sel_config);
        }
        this.refresh();
      })

    })

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


  //add_image_to_layer ajouter une image
  on_upload(evt: any,layer:Layer) {

    let body={
      filename:evt.filename,
      "content":evt.file,
      "type":evt.type
    }

    if(body.filename.endsWith("svg")){
      this.network.generate_svg(evt.file,this.text_to_add,layer.name).subscribe((r:any)=>{
        layer.elements=[];
        for(let img of r)
          layer.elements.push({"image":img,"name":normalize(evt.filename)});
      })
    }else{
      this.network.wait("Chargement des visuels");
      this.network.upload(body,this.sel_platform).subscribe((r:any)=>{
        this.network.wait();
        layer.elements.push({image:r.url,name:normalize(evt.filename)});
      },(err:any)=>{
        showError(this,err);
      })
    }
  }



  add_layer(name="",force=false) {
    if(name.length == 0)name="layer"+this.layers.length;

    let new_layer={
      params:{},
      name:name,
      elements:[],
      text:"",
      unique:false,
      indexed:true,
      position:this.layers.length,
      translation: {x:0,y:0},
      scale: {x:1,y:1}
    }

    if(force){
      this.layers.push(new_layer)
    } else {
      _prompt(this,"Nom du calque ?",name).then((name)=> {
        new_layer.name = name;
        this.layers.push(new_layer)
      });
    }

  }


  fill_layer(i:number,w:number,h:number,preview:number,func:Function){
    this.network.wait("Composition de " + i + " calques sur " + this.layers.length);
    this.network.add_layer(this.layers[i],w,h,preview).subscribe(()=> {
      i = i + 1;
      if(i<this.layers.length){
        this.fill_layer(i,w,h,preview,func);
      }else{
        func();
      }
    },(err)=>{showError(this,err)});
  }


  url_collection="";
  generate_collection(format="zip") {

    //Vérification du format des datas
    if(this.data.properties && this.data.properties!=""){
      for(let line of this.data.properties.split("\n")){
        if(line.split("=").length!=2){
          showMessage(this,"Format des propriétés/attributs incorrect. La syntaxe doit être attribut=valeur pour chaque ligne");
          return;
        }
      }
    }


    let i=0;

    this.network.reset_collection().subscribe(()=>{
      this.fill_layer(i,format=="preview" ? 200 : 0,format=="preview" ? 200 : 0,0,()=>{

        this.data.sequence=this.text_to_add.split("|");
        if(this.operation!.sel_ope!.nftlive){
          this.data.operation=this.operation.sel_ope?.id;
        }

        this.network.wait("Fabrication de la collection ...");
        showMessage(this,"L'aperçu se limite à 10 NFT maximum");

        this.network.get_collection(Math.min(this.limit,10),this.filename_format,this.sel_ext,this.col_width+","+this.col_height,this.seed,this.quality,"preview",this.data).subscribe((r:any)=>{
          this.show_download_link();
          this.network.wait("");
          this.previews=r;
        },(err)=>{showError(this,err);})


        // if(format=="upload"){
        //   this.network.wait("");
        //   this.network.get_collection(Math.min(this.limit,50),this.filename_format,this.sel_ext,this.col_width+","+this.col_height,this.seed,this.quality,"upload",this.data,this.sel_platform).subscribe((r:any) => {
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


  //Génére un sticker sur la base d'un texte et l'ajoute à la layer l
  generate(l:Layer){
    l.params={
      text:this.text_to_add,
      x:this.position_text.x,
      y:this.position_text.y,
      font:{
        name:this.fontfiles,
        size:this.fontsize,
        color:this.color
      }
    }
    if(l==null){
      showMessage(this,"Vous devez sélectionner la couche cible pour créer le visuel");
      return;
    }

    let i=0;
    for(let txt of this.text_to_add.split("|")){
      if(txt.length>0){
        if(i==this.sel_colors.length)i=0;
        let elt=this.create_element(txt);
        if(this.usePalette)elt.fontstyle.color=this.sel_colors[i];
        l.elements.push({"text":elt});
        i=i+1;
      }
    }

    this.network.wait("Génération de la série d'images")
    this.network.update_layer(l,20).subscribe((r:any)=>{
      this.network.wait("");
      l.elements=r.elements;
    },(err)=>{
      showError(this,err);
    });
  }


  onclick_on_text($event: MouseEvent,l:Layer) {
    this.position_text={x:$event.offsetX/2,y:$event.offsetY/2}
  }



  modify_element($event:MouseEvent, layer: Layer, element:any) {
    if($event.button==0){
      $event.stopPropagation();
      let pos=layer.elements.indexOf(element);
      if($event.ctrlKey){
        layer.elements.splice(pos,1);
      }

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
    let idx=this.layers.indexOf(layer);
    if(layer.position+variation>=0 && layer.position<=this.layers.length){
      this.layers[idx+variation].position=this.layers[idx+variation].position-variation
      layer.position=layer.position+variation;
      this.sort_layers();
    }
  }



  delete_layer(layer: Layer) {
    let pos=this.layers.indexOf(layer);
    this.layers.splice(pos,1);
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



  build_sample(layers:any[],data={},reset=true) {
    if(reset)this.layers=[];

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
        this.layers.push(layer);
        if(this.layers.length==layers.length)this.sort_layers();
      });

      this.data=data;

    }

  }


  sort_layers(){
    this.layers.sort((l1,l2) => {if(l1.position>l2.position)return 1; else return -1;})
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


  load_config(name="config") {
    if(name){
      this.network.wait("Chargement de "+name+" en cours ...");
      this.config_name=name;
      this.sel_config=name+".yaml";
      this._location.replaceState("./creator?config="+name);
      this.network.load_config(name).subscribe((r:any)=>{
        this.sel_platform=r.platform;
        if(r.layers){
          for(let l of r.layers){
            for(let e of l.elements){
              if(this.sel_platform=="nfluent")e.image=e.image.replace("http://127.0.0.1:4242/","https://server.nfluent.io:4242/");
              if(this.sel_platform=="nfluent local")e.image=e.image.replace("https://server.nfluent.io:4242/","http://127.0.0.1:4242/");
            }
          }

          this.layers=r.layers;
          this.data=r.data || {
            title:"MonTitre",
            symbol:"token__idx__",
            description:"madescription",
            collection:"macollection",
            properties:"propriete=valeur",
            files:"http://monfichier"
          };
          if(!this.data.hasOwnProperty("nftlive"))this.data.nftlive={datestart:"",timestart:"",duration:120};

          this.col_width=r.width;
          this.col_height=r.height;
          this.filename_format=r.filename_format;
          this.limit=r.limit;
          this.seed=r.seed || 0;
          this.position_text.x=r.x || 10;
          this.text_to_add=r.text_to_add || "";
          this.position_text.y=r.y || 10;
          this.fontsize=r.fontstyle.size;
          this.font=this.find_font(r.fontstyle.name);
          this.color=r.fontstyle.color
        }
        this.previews=[];
      },(err=>{
        showError(this,err);
        this.reset()
      }),()=>{
        this.network.wait("");
      });
    }
  }

  //https://server.f80lab.com/api/configs/?format=file
  quality=98;
  config_with_image=true;
  data: any={};


  save_config(with_file=false) : Promise<string> {
    return new Promise((resolve,reject) => {
      let body = {
        layers: this.layers,
        width: this.col_width,
        height: this.col_height,
        x: this.position_text.x,
        y: this.position_text.y,
        seed: this.seed,
        text_to_add: this.text_to_add,
        limit: this.limit,
        filename_format: this.filename_format,
        platform: this.sel_platform,
        nftlive:this.data.nftlive,
        fontstyle: {
          name: this.font.file,
          color: this.color,
          size: this.fontsize
        },
        data: this.data
      }

      for (let l of body.layers) {
        if(l.elements){
          for (let f of l.elements)
            f = "\"" + f + "\""
        } else {
          reject("Couche invalide");
        }
      }

      this.config_name = this.config_name.replace(".yaml.yaml", ".yaml");
      this.network.save_config_on_server(this.config_name, body).subscribe(() => {
        this.sel_config = this.config_name;
        setTimeout(() => {
          this.refresh()
        }, 1000);
        if(with_file)open(environment.server + "/api/configs/" + this.config_name + "/?format=file", "config");
        resolve("ok")
      });
    });
  }


  on_upload_config($event: any) {
    this.network.wait("Chargement du fichier de configuration");
    this.network.save_config_on_server($event.filename,$event.file).subscribe(()=>{
      this.network.wait("");
      this.sel_config=$event.filename;
      this.load_config($event.filename);
    },(err)=>{
      showError(this);
    })
  }

  add_serial(layer: Layer) {
    _prompt(this,"Début de la série","1","","number").then((txtStart:string)=>{
      _prompt(this,"Fin de la série","100","","number").then((txtEnd:string)=> {
        let modele=this.text_to_add;
        if(modele.indexOf("_idx_")==-1)modele=modele+"_idx_";
        this.text_to_add="";
        let nbr_digits=txtEnd.length;
        for(let i=Number(txtStart);i<=Number(txtEnd);i++){
          this.text_to_add=this.text_to_add+modele.replace("_idx_",i.toString().padStart(nbr_digits,'0'))+"|";
        }
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
        name: this.font.file,
        color: this.color,
        size: this.fontsize
      },
      dimension:[this.col_width, this.col_height],
      x: Number(this.position_text.x),
      y: Number(this.position_text.y),
    }
  }

  generate_with_color(layer: Layer) {
    this.network.clone_with_color(layer,this.color,this.sel_palette).subscribe((images:any)=>{
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
      this.position_text.x=l.params.x;
      this.position_text.y=l.params.y;
      this.text_to_add=l.params.text;
      this.color=l.params.font.color;
      this.fontsize=l.params.font.size;
    }
  }

  new_conf(){
    _prompt(this,"Nom de la configuration").then((resp)=>{
      this.add_layer("fond",true);
      this.add_layer("image",true);
      this.add_layer("texte",true);
      this.config_name=resp;
      this._location.replaceState("/creator?config="+resp);
    })
  }

  init_data(){
    this.data={
      title:"MonTitre",
      symbol:"token__idx__",
      description:"madescription",
      collection:"macollection",
      properties:"propriete=valeur",
      files:"http://monfichier",
      operation:""}
  }

  reset(new_conf=true) {
    _prompt(this,"Effacer la configuration actuelle ?","","","","ok","annuler",true).then(()=>{
      this.layers=[];
      this._location.replaceState("./creator");
      this.config_name="";
      this.init_data();
      if(new_conf)this.new_conf();
    })
  }

  find_image() {
    _prompt(this,"Terme à trouver").then((resp)=>{
      open("https://www.google.com/search?q=google%20image%20"+resp+"&tbm=isch&tbs=ic:trans","search_google");
      open("https://emojipedia.org/search/?q="+resp,"search_emoji")
      open("https://pixabay.com/fr/vectors/search/"+resp+"/","search_vector")
      open("https://thenounproject.com/search/icons/?iconspage=1&q="+resp,"search_vector")
      open("https://pixabay.com/images/search/"+resp+"/?colors=transparent","search_transparent")
      open("https://www.pexels.com/fr-fr/chercher/"+resp+"/","search_pexels")
      open("https://all-free-download.com/free-vector/"+resp+".html/","search_vectors")
    })
  }

  paste_picture(layer: Layer) {
    navigator.clipboard.read().then((content)=>{
      for (const item of content) {
        if (!item.types.includes('image/png')) {
          showMessage(this,"Ce contenu ne peut être intégré. Enregistrez l'image sur votre ordinateur et importez là ensuite");
        }
        item.getType('image/png').then((blob)=>{
          let reader = new FileReader();
          reader.readAsDataURL(blob)
          reader.onload=()=>{
            let s=reader.result;
            this.network.upload(s,this.sel_platform,blob.type).subscribe((r:any)=>{
              layer.elements.push({image:r.url});
              this.network.wait("")
            },()=>{showError(this);})
          }
        },()=>{

        })
      }
    })
  }

  async del_config(sel_config: any) {
    this.network.del_config(sel_config).subscribe(()=>{
      showMessage(this,"Configuration supprimé");
      this.load_configs();
      this._location.replaceState("/creator");
      this.refresh();
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
      this.network.add_layer(layer,this.col_width,this.col_height).subscribe(()=> {
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

  show_download_link() {
    showMessage(this,"Télécharger sur le lien pour démarrer la fabrication et le téléchargement de la collection")
    this.url_collection=environment.server+"/api/collection/?seed="+this.seed+"&image="+this.sel_ext
      +"&size="+this.col_width+","+this.col_height+"&name="+this.filename_format
      +"&format=zip&limit="+this.limit+"&quality="
      +this.quality+"&data="+btoa(encodeURIComponent(JSON.stringify(this.data)));
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
      this.network.upload_attributes(this.config_name,$event.file.split("base64,")[1]).subscribe((resp:any)=>{
        showMessage(this,"Fichier d'attributs associés")
      })
    });
  }

  clear_data() {
    this.data = {
      title: "",
      symbol: "",
      description: "",
      collection: "",
      properties: "",
      files: ""
    }
  }

  async new_config() {
    let name=_prompt(this,"Nom de la configuration","maconfig");
    this.config_name=await name;

    await this.save_config(false);
    await this.load_configs();
    await this.load_config(this.config_name);
  }
}
