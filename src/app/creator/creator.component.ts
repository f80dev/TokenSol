import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {$$, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PLATFORMS} from "../../definitions";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from "@angular/common";
import {MatSelectChange} from "@angular/material/select";

export interface Layer {
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
    public toast:MatSnackBar,
    public safe:SafePipe,
    public _location:Location
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


  on_upload(evt: any,layer:Layer) {
    let body={
      filename:evt.filename,
      "content":evt.file,
      "type":evt.type
    }

    this.network.upload(body,this.sel_platform).subscribe((r:any)=>{
      layer.elements.push({image:r.url});
    })
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
      this.layers.push({
        name:name,
        elements:[],
        text:"",
        unique:false,
        indexed:true,
        position:this.layers.length
      })
    });
  }


  fill_layer(i:number,w:number,h:number,preview:number,func:Function){
    this.message = "Composition de " + i + " calques sur " + this.layers.length;
    this.network.add_layer(this.layers[i],w,h,preview).subscribe(()=> {
      i = i + 1;
      if(i<this.layers.length){
        this.fill_layer(i,w,h,preview,func);
      }else{
        func();
      }
    });
  }


  generate_collection(format="zip") {
    let i=0;
    this.show_collection=false;
    this.network.reset_collection().subscribe(()=>{
      this.fill_layer(i,format=="preview" ? 200 : 0,format=="preview" ? 200 : 0,0,()=>{
        if(format=="zip"){
          this.message="";
          open(environment.server+"/api/collection/?seed="+this.seed+"&image="+this.sel_ext+"&size="+this.col_width+","+this.col_height+"&name="+this.filename_format+"&format=zip&limit="+this.limit,"_blank")
        }

        if(format=="preview"){
          this.message="Fabrication de la collection en cours ...";
          this.network.get_collection(Math.min(this.limit,50),this.filename_format,this.sel_ext,this.col_width+","+this.col_height,this.seed).subscribe((r:any)=>{
            this.message="";
            this.previews=r;
          },(err)=>{showError(this,err);})
        }

        if(format=="upload"){
          this.message="";
          open(environment.server+"/api/collection/?format=upload&platform="+this.sel_platform+"&limit="+this.limit,"_blank")
        }
      });
    },(err)=>{showError(this,err);})
  }


  //Génére un sticker sur la base d'un texte et l'ajoute à la layer l
  generate(l:Layer){
    if(l==null){
      showMessage(this,"Vous devez sélectionner la couche cible pour créer le visuel");
      return;
    }

    let i=0;
    for(let txt of this.text_to_add.split("|")){
      if(i==this.sel_colors.length)i=0;
      let elt=this.create_element(txt);
      if(this.usePalette)elt.fontstyle.color=this.sel_colors[i];
      l.elements.push({"text":elt});
      i=i+1;
    }

    this.message="Génération de la série d'images"
    this.network.update_layer(l,20).subscribe((r:any)=>{
      this.message="";
      l.elements=r.elements;
    },(err)=>{
      showError(this,err);
    });
  }


  onclick_on_text($event: MouseEvent,l:Layer) {
    this.position_text={x:$event.offsetX/2,y:$event.offsetY/2}
  }

  remove_element($event:MouseEvent, layer: Layer, element:any) {
    if($event.button==0 && $event.ctrlKey){
      $event.stopPropagation();
      let pos=layer.elements.indexOf(element);
      layer.elements.splice(pos,1);
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
          layer.elements.push(url);
        }
      }
    });
  }



  build_sample(layers:any[],reset=true) {
    if(reset)this.layers=[];

    for(let l of layers){
      $$("Mise a jour des noms de fichier avec le chemin complet");
      for(let k=0;k<100;k++)l["files"]=l["files"].replace("$appli$",environment.appli);

      let layer:Layer={
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
      this.config_name=name;
      this._location.replaceState("./creator?config="+name);
      this.network.load_config(name).subscribe((r:any)=>{
        this.layers=r.layers;
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
        this.previews=[];
      },(err=>{
        showError(this,err);
        this._location.replaceState("./creator");
      }));
    }
  }

  //https://server.f80lab.com/api/configs/?format=file


  save_config() {
    let body={
      layers: this.layers,
      width:this.col_width,
      height:this.col_height,
      x:this.position_text.x,
      y:this.position_text.y,
      seed:this.seed,
      text_to_add:this.text_to_add,
      limit:this.limit,
      filename_format:this.filename_format,
      platform:this.sel_platform,
      fontstyle:{
        name:this.font.file,
        color:this.color,
        size:this.fontsize
      }
    }
    for(let l of body.layers){
      for(let f of l.elements)
        f="\""+f+"\""
    }
    this.config_name=this.config_name.replace(".yaml.yaml",".yaml");
    this.network.save_config_on_server(this.config_name,body).subscribe(()=>{
      this.sel_config=this.config_name;
      setTimeout(()=>{this.refresh()},1000);
      open(environment.server+"/api/configs/"+this.config_name+"/?format=file","config");
    });
  }


  on_upload_config($event: any) {
    this.message="Chargement du fichier de configuration";
    let txt=atob($event.file.split("base64,")[1]);
    this.network.save_config_on_server($event.filename,txt).subscribe(()=>{
      this.message="";
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
}
