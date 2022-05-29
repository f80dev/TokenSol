import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {SafePipe} from "../safe.pipe";
import {environment} from "../../environments/environment";
import {showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PLATFORMS} from "../../definitions";
import {ActivatedRoute, Router} from "@angular/router";
import {Location} from "@angular/common";

export interface Layer {
  unique: boolean
  indexed: boolean
  name:string
  position:number
  files:any[]
  text:string
  width:number
  height:number
  fontstyle: {
    name:string
    size:number
    color:string
  }
}

@Component({
  selector: 'app-creator',
  templateUrl: './creator.component.html',
  styleUrls: ['./creator.component.css']
})
//test : http://localhost:4200/creator

export class CreatorComponent implements OnInit {
  layers: Layer[]=[];
  col_width=500;
  backcolor="black";
  col_height=500;
  platforms=PLATFORMS;
  limit=10;
  show_addtext:any;
  configs:string[]=[];
  previews:any[]=[];
  text_to_add: string="Texte ici";
  fontsize: number=100;
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
      layer.files.push(r.url);
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
        files:[],
        text:"",
        unique:false,
        indexed:true,
        position:this.layers.length,
        width:this.col_width,
        height:this.col_height,
        fontstyle:{
          name:this.font.file,
          size:this.fontsize,
          color:this.color
        }
      })
    });
  }


  fill_layer(i:number,w:number,h:number,func:Function){
    this.message = "Composition de " + i + " calques sur " + this.layers.length;
    this.network.add_layer(this.layers[i],w,h).subscribe(()=> {
      i = i + 1;
      if(i<this.layers.length){
        this.fill_layer(i,w,h,func);
      }else{
        func();
      }
    });
  }


  generate_collection(format="zip") {
    let i=0;
    this.show_collection=false;
    this.network.reset_collection().subscribe(()=>{
      this.fill_layer(i,format=="preview" ? 200 : 0,format=="preview" ? 200 : 0,()=>{
        if(format=="zip"){
          this.message="";
          open(environment.server+"/api/collection/?image="+this.sel_ext+"&size="+this.col_width+","+this.col_height+"&name="+this.filename_format+"&format=zip&limit="+this.limit,"_blank")
        }

        if(format=="preview"){
          this.message="Fabrication de la collection en cours ...";
          this.network.get_collection(this.limit,this.filename_format,this.sel_ext).subscribe((r:any)=>{
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


  generate(l:Layer){
    if(l==null){
      showMessage(this,"Vous devez sélectionner la couche cible pour créer le visuel");
      return;
    }
    l.fontstyle={
      name:this.font.file,
      color:this.color,
      size:this.fontsize
    }
    this.network.create_text_layer(this.position_text.x,this.position_text.y,this.text_to_add,l).subscribe((r:any)=>{
      for(let image of r.images)
        l.files.push(image);
    });
  }


  onclick_on_text($event: MouseEvent,l:Layer) {
    this.position_text={x:$event.offsetX/2,y:$event.offsetY/2}
  }

  remove_file($event:MouseEvent, layer: Layer, file: File) {
    if($event.button==0 && $event.ctrlKey){
      $event.stopPropagation();
      let pos=layer.files.indexOf(file);
      layer.files.splice(pos,1);
      this.network.add_layer(layer).subscribe(()=>{
        showMessage(this,"Mise a jour");

      });

    }

  }

  update_position(layer: Layer, variation:number) {
    let idx=this.layers.indexOf(layer);
    if(layer.position+variation>=0 && layer.position<=this.layers.length){
      this.layers[idx+variation].position=this.layers[idx+variation].position-variation
      layer.position=layer.position+variation;
      this.layers.sort((l1,l2) => {if(l1.position>l2.position)return 1; else return -1;})
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
          layer.files.push(url);
        }
      }
    });
  }



  build_sample(samples:any[],reset=true) {
    if(reset)this.layers=[];
    let fontstyle={name:this.font.file, color:this.color,size:this.fontsize}
    let i=this.layers.length;
    for(let sample of samples){
      for(let k=0;k<100;k++)sample["files"]=sample["files"].replace("$appli$",environment.appli);

      let layer:Layer={
        name:sample.hasOwnProperty("name") ? sample.name : "layer"+i,
        files:sample["files"].length>0 ? sample["files"].split(",") : [],
        text:sample["text"],
        unique:false,
        indexed:true,
        position:i,
        width:this.col_width,height:this.col_height,
        fontstyle:fontstyle
      }

      if(sample["text"].length>0){
        this.network.create_text_layer(25,40,sample["text"],layer).subscribe((r:any)=>{
          layer.files=r.images;
          this.layers.push(layer);
        });
      } else {
        this.layers.push(layer);
      }

      i=i+1;
    }
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
  sel_ext: string="webp";
  save_config() {
    let body={
      layers: this.layers,
      width:this.col_width,
      height:this.col_height,
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
      for(let f of l.files)
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
    for(let f of layer.files){
      if(f.indexOf("/api/images/")>-1){
        let id=f.split("/api/images/")[1].split("?")[0];
        this.network.remove_image(id).subscribe(()=>{});
      }

    }
    layer.files=[];
  }




  open_file(file: any) {
    open(file,"preview");
  }
}
