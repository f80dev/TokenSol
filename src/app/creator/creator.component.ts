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
  fontstyle:any
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
  col_height=500;
  platforms=PLATFORMS;
  limit=10;
  show_addtext:any;
  configs:string[]=[];
  previews:any[]=[];
  text_to_add: string="Texte ici";
  fontsize: number=100;
  color: any="#000000";
  fontname: string="corbel.ttf"
  sel_platform: any="nftstorage";
  sel_config: any="";
  fontfiles: any;
  position_text: { x: any; y: any }={x:10,y:10};
  filename_format: string ="visual__idx__.png";
  show_collection: boolean=false;
  message="";

  constructor(
    public network:NetworkService,
    public dialog:MatDialog,
    public router:Router,
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public safe:SafePipe,
    public _location:Location
  ) {}


  ngOnInit(): void {
    this.layers=[];
    this.build_sample([{files:"",text:""},{files:"",text:""},{files:"",text:""}]);
    this.network.list_config().subscribe((r:any)=>{
      this.configs=r.files;
      this.sel_config=this.routes.snapshot.queryParamMap.get("config") || this.configs[0];
      this.load_config(this.sel_config);
    })
    this.network.list_installed_fonts().subscribe((r:any)=>{
      this.fontfiles=r.fonts;
    })

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
          name:this.fontname,
          size:this.fontsize,
          color:this.color
        }
      })
    });
    }



  generate_collection(format="zip") {
    let i=0;
    this.show_collection=false;
    this.network.reset_collection().subscribe(()=>{
      for(let l of this.layers){
        this.network.add_layer(l).subscribe(()=>{
          i=i+1;
          if(i==this.layers.length){
            if(format=="zip")
              open(environment.server+"/api/collection/?size="+this.col_width+","+this.col_height+"&name="+this.filename_format+"&format=zip&limit="+this.limit,"_blank")

            if(format=="preview"){
              this.message="Fabrication de la collection en cours ...";
              this.network.get_collection(this.limit,this.filename_format).subscribe((r:any)=>{
                this.message="";
                this.previews=r;
              },(err)=>{showError(this,err);})
            }

            if(format=="upload"){
              open(environment.server+"/api/collection/?format=upload&platform="+this.sel_platform+"&limit="+this.limit,"_blank")
            }

          }
        });
      }
    })
  }


  generate(l:Layer){
    if(l==null){
      showMessage(this,"Vous devez sélectionner la couche cible pour créer le visuel");
      return;
    }
    this.network.create_text_layer(this.position_text.x,this.position_text.y,this.text_to_add,l).subscribe((r:any)=>{
      for(let image of r.images)
        l.files.push(image);
    });
  }


  onclick_on_text($event: MouseEvent,l:Layer) {
    this.position_text={x:$event.offsetX,y:$event.offsetY}
  }

  remove_file(layer: Layer, file: File) {
    let pos=layer.files.indexOf(file);
    layer.files.splice(pos,1);
    this.network.add_layer(layer).subscribe(()=>{
      showMessage(this,"Mise a jour");
    });
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
    let fontstyle={name:this.fontname, color:this.color,size:this.fontsize}
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


  load_config(name="config") {
    if(name){
      this.network.load_config(name).subscribe((r:any)=>{
        this.layers=r.layers;
        this.col_width=r.width;
        this.col_height=r.height;
        this.filename_format=r.filename_format;
        this.limit=r.limit;
        this.sel_platform=r.platform;
        this.show_collection=true;
      },(err=>{showError(this,err)}));
    }
  }


  save_config() {
    let body={
      layers: this.layers,
      width:this.col_width,
      height:this.col_height,
      limit:this.limit,
      filename_format:this.filename_format,
      platform:this.sel_platform
    }
    for(let l of body.layers){
      for(let f of l.files)
        f="\""+f+"\""
    }
    let name="config";
    this.network.save_config_on_server(name,body).subscribe(()=>{
      open(environment.server+"/api/configs/"+name+"/?format=file","config");
    })
  }


  on_upload_config($event: any) {
    this.message="Chargement du fichier de configuration";
    let txt=atob($event.file.split("base64,")[1]);
    this.network.save_config_on_server($event.filename,txt).subscribe(()=>{
      this.message="";
      this._location.replaceState("./creator?config="+$event.filename);
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
        for(let i=start;i<=end;i++){
          this.text_to_add=this.text_to_add+modele.replace("__idx__",String(i))+"|";
        }
      });
    });
  }

  clear_layer(layer: Layer) {
    layer.files=[];
  }

  upload_on_storage_platform() {

  }


  open_file(file: any) {
    open(file,"preview");
  }
}
