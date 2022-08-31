import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {$$, setParams, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PLATFORMS, PRICE_PER_TOKEN, TOKEN_FACTORY_WALLET} from "../../definitions";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from "@angular/common";
import {MatSelectChange} from "@angular/material/select";
import {ClipboardModule} from "@angular/cdk/clipboard";
import {UserService} from "../user.service";

export interface Layer {
  params: any;
  unique: boolean
  indexed: boolean
  name:string
  position:number
  elements:any[]
  text:string
}

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
  show_collection: boolean=false;
  message="";
  max_items: number=8;
  config_name: string="maconfig";
  palette: any={};

  constructor(
    public network:NetworkService,
    public dialog:MatDialog,
    public router:Router,
    public routes:ActivatedRoute,
    public user:UserService,
    public toast:MatSnackBar,
    public safe:SafePipe,
    public _location:Location,
    public clipboard:ClipboardModule
  ) {}



  refresh(){
    this.network.list_config().subscribe((r:any)=>{
      this.configs=r.files;
      if(!this.sel_config && r.files.length>0){
        this.sel_config=this.routes.snapshot.queryParamMap.get("config") || this.configs[0];
        this.load_config(this.sel_config);
      }
    })
    this.network.list_installed_fonts().subscribe((r:any)=>{
      this.fontfiles=r.fonts;
      this.font=r.fonts[0];
    })
  }



  ngOnInit(): void {
      if(environment.appli.indexOf("127.0.0.1")>-1 || environment.appli.indexOf("localhost")>-1)this.sel_platform="nfluent_local"
      this.layers=[];
      this.build_sample([{files:"",text:""},{files:"",text:""},{files:"",text:""}]);
      this.network.get_palettes().subscribe((p)=>{
        this.palette_names=Object.keys(p);
        this.palette=p;
        this.sel_palette=this.palette_names[0];
      })
      this.refresh();

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
        this.user.wallet.sendTransaction(TOKEN_FACTORY_WALLET, nTokenToMint * PRICE_PER_TOKEN).then((result) => {
          showMessage(this, "Paiement ok");
          resolve(result);
        }).catch(()=>{reject();})
      }

    });
  }



  on_upload(evt: any,layer:Layer) {
    let body={
      filename:evt.filename,
      "content":evt.file,
      "type":evt.type
    }

    if(body.filename.endsWith("yaml")){
      this.network.generate_svg(evt.file).subscribe((r:any)=>{
        for(let img of r)
          layer.elements.push({image:img});
      })
    }else{
      this.network.upload(body,this.sel_platform).subscribe((r:any)=>{
        layer.elements.push({image:r.url});
      })
    }
  }

  add_layer() {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Nom du calque ?",
          type: "text",
          result:"layer"+this.layers.length,
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((name:string) => {
      if(name && name.length>2){
        this.layers.push({
          params:{},
          name:name,
          elements:[],
          text:"",
          unique:false,
          indexed:true,
          position:this.layers.length
        })
      }
    });
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
    let i=0;
    this.show_collection=false;
    this.network.reset_collection().subscribe(()=>{
      this.fill_layer(i,format=="preview" ? 200 : 0,format=="preview" ? 200 : 0,0,()=>{


        if(format=="zip"){
          this.network.wait("");
          //this.user.connect().then((profil:any)=>{
            //this.paiement(this.limit,profil).then(()=>{
              this.url_collection=environment.server+"/api/collection/?seed="+this.seed+"&image="+this.sel_ext+"&size="+this.col_width+","+this.col_height+"&name="+this.filename_format+"&format=zip&limit="+this.limit+"&quality="+this.quality;
              this.url_collection=this.url_collection+"&data="+btoa(JSON.stringify(this.data))
            //});
          //});
        }

        if(format=="preview"){
          this.network.wait("Fabrication de la collection en cours ...");
          this.network.get_collection(Math.min(this.limit,50),this.filename_format,this.sel_ext,this.col_width+","+this.col_height,this.seed,this.quality,"preview",this.data).subscribe((r:any)=>{
            this.network.wait("");
            this.previews=r;
          },(err)=>{showError(this,err);})
        }

        if(format=="upload"){
          this.network.wait("");
          this.network.get_collection(Math.min(this.limit,50),this.filename_format,this.sel_ext,this.col_width+","+this.col_height,this.seed,this.quality,"upload",this.data,this.sel_platform).subscribe((r:any) => {
            this.upload_files=[];
            for(let item of r){
              // @ts-ignore
              this.upload_files.push(item['url']);
            }
          });

        }
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
    for(let f of this.fontfiles){
      if(f.file==filename)
        return f;
    }
    return null;
  }


  load_config(name="config") {
    if(name){
      this.network.wait("Chargement en cours ...");
      this.config_name=name;
      this._location.replaceState("./creator?config="+name);
      this.network.load_config(name).subscribe((r:any)=>{
        if(r.layers){
          for(let l of r.layers){
            for(let e of l.elements){
              if(this.sel_platform=="nfluent")e.image=e.image.replace("http://127.0.0.1:4242/","https://server.nfluent.io:4242/");
              if(this.sel_platform=="nfluent local")e.image=e.image.replace("https://server.nfluent.io:4242/","http://127.0.0.1:4242/");
            }
          }

          this.layers=r.layers;
          this.data=r.data || {title:"MonTitre",symbol:"token__idx__",description:"madescription",collection:"macollection",family:"mafamille",properties:"propriete=valeur",files:"http://monfichier"};
          this.col_width=r.width;
          this.col_height=r.height;
          this.filename_format=r.filename_format;
          this.limit=r.limit;
          this.seed=r.seed || 0;
          this.position_text.x=r.x || 10;
          this.text_to_add=r.text_to_add || "";
          this.position_text.y=r.y || 10;
          this.sel_platform=r.platform;
          this.show_collection=true;
          this.fontsize=r.fontstyle.size;
          this.font=this.find_font(r.fontstyle.name);
          this.color=r.fontstyle.color;
        }

        this.previews=[];
        this.network.wait("");
      },(err=>{
        showError(this,err);
        this._location.replaceState("./creator");
      }));
    }
  }

  //https://server.f80lab.com/api/configs/?format=file
  quality=98;
  config_with_image=true;
  data: any={title:"MonTitre",symbol:"token__idx__",description:"madescription",collection:"macollection",family:"mafamille",properties:"propriete=valeur",files:"http://monfichier"};


  save_config() {
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
        fontstyle: {
          name: this.font.file,
          color: this.color,
          size: this.fontsize
        },
        data: this.data
      }

      for (let l of body.layers) {
        for (let f of l.elements)
          f = "\"" + f + "\""
      }
      this.config_name = this.config_name.replace(".yaml.yaml", ".yaml");
      this.network.save_config_on_server(this.config_name, body).subscribe(() => {
        this.sel_config = this.config_name;
        setTimeout(() => {
          this.refresh()
        }, 1000);
        open(environment.server + "/api/configs/" + this.config_name + "/?format=file", "config");
        resolve("ok")
      });
    });
  }


  on_upload_config($event: any) {
    this.network.wait("Chargement du fichier de configuration");
    let txt=atob($event.file.split("base64,")[1]);
    this.network.save_config_on_server($event.filename,txt).subscribe(()=>{
      this.network.wait("");
      this.load_config($event.filename);
    },(err)=>{
      showError(this);
    })
  }

  add_serial(layer: Layer) {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Début de la série",
          type: "number",
          result:"1",
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((start:number) => {
      this.dialog.open(PromptComponent,{
        width: 'auto',data:
          {
            title: "Fin de la série",
            type: "number",
            result:100,
            onlyConfirm:false,
            lbl_ok:"Ok",
            lbl_cancel:"Annuler"
          }
      }).afterClosed().subscribe((end:number) => {
        let modele=this.text_to_add;
        if(modele.indexOf("__idx__")==-1)modele=modele+"__idx__";
        this.text_to_add="";
        let nbr_digits=end.toString().length;
        for(let i=start;i<=end;i++){
          this.text_to_add=this.text_to_add+modele.replace("__idx__",i.toString().padStart(nbr_digits,'0'))+"|";
        }
      });
    });
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

  reset() {
    this.save_config().then(()=>{
      this.layers=[]
      this.config_name=""
      this._location.replaceState("/creator");
    });
  }

  find_image() {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Terme à trouver",
          type: "text",
          value:"",
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe(resp => {
      if(resp){
        open("https://www.google.com/search?q=google%20image%20"+resp+"&tbm=isch&tbs=ic:trans","search_google");
        open("https://emojipedia.org/search/?q="+resp,"search_emoji")
        open("https://pixabay.com/fr/vectors/search/"+resp+"/","search_vector")
        open("https://pixabay.com/images/search/"+resp+"/?colors=transparent","search_transparent")
        open("https://www.pexels.com/fr-fr/chercher/"+resp+"/","search_pexels")
        open("https://all-free-download.com/free-vector/"+resp+".html/","search_vectors")
      }
    });
  }

  paste_picture(layer: Layer) {
    navigator.clipboard.read().then((content)=>{
      for (const item of content) {
        if (!item.types.includes('image/png')) {throw new Error('Clipboard contains non-image data.');}
        item.getType('image/png').then((blob)=>{
          let reader = new FileReader();
          reader.readAsDataURL(blob)
          reader.onload=()=>{
            let s=reader.result;
            this.network.upload(s,this.sel_platform,blob.type).subscribe((r:any)=>{
              layer.elements.push({image:r.url});
              this.network.wait("")
            })
          }
        })
      }
    })
  }

  del_config(sel_config: any) {
    this.network.del_config(sel_config).subscribe(()=>{
      showMessage(this,"Configuration supprimé");
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
    this.dialog.open(PromptComponent, {
      width: 'auto', data:
        {
          title: "Choisir un filtre",
          type: "list",
          options:filters,
          value:"blur",
          onlyConfirm: false,
          lbl_ok: "Ok",
          lbl_cancel: "Annuler"
        }
    }).afterClosed().subscribe((filter: string) => {
      if(filter){
        this.network.add_layer(layer,this.col_width,this.col_height).subscribe(()=> {
          this.network.apply_filter(layer.name,filter).subscribe((r:any)=>{
            for(let i of r.images)
              layer.elements.push({image:i})
            this.refresh();
          })
        });
      }

    });
  }

  miner() {
    this.router.navigate(["miner"],{queryParams:{param:setParams({files:this.upload_files})}})
  }
}
