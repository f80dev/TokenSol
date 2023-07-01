import {Component, EventEmitter, Input, OnChanges, Output, SimpleChanges} from '@angular/core';
import {$$, open_image_banks, setParams} from "../../tools";
import {DeviceService} from "../device.service";
import {NgNavigatorShareService} from "ng-navigator-share";
import {MatDialog} from "@angular/material/dialog";

export function genlink_to_obj(links:any[]){
  let obj:any={}
  for(let l of links){
    obj[l.name]=l.value;
  }
  return obj
}

@Component({
  selector: 'app-genlink',
  templateUrl: './genlink.component.html',
  styleUrls: ['./genlink.component.css']
})
export class GenlinkComponent implements OnChanges {

  @Input() properties: any[]=[];
  @Input() domain: string="";
  @Input() title: string="";
  url: string="";
  @Input() show_command_panel: boolean = true;
  @Output('update') onupdate: EventEmitter<any>=new EventEmitter();

  constructor(
      public device:DeviceService,
      public dialog:MatDialog,
      public ngShare:NgNavigatorShareService
  ) {

  }

  ngOnChanges(changes: SimpleChanges): void {
    this.create_url()
  }


  save_local(){
    this.create_url();
    localStorage.setItem("config_"+this.domain,JSON.stringify(this.properties))
  }

  load_local(){
    this.properties=JSON.parse(localStorage.getItem("config_"+this.domain) || "{}");
  }


  create_url() {
    let obj:any={}
    for(let p of this.properties){
      if(typeof(p.value)=="object"){
        obj[p.name]=p.value.value
      }else{
        obj[p.name]=p.value
      }
      if(p.type=="list" && !p.hasOwnProperty("value")){
        let idx=this.properties.indexOf(p);
        this.properties[idx].value={label:p.options[0],value:p.options[0]}
      }
    }
    obj["toolbar"]=false;
    $$("Enregistrement des parametres ",obj)
    let prefix=this.domain.endsWith("/") ? "?" : "/?"
    this.url=this.domain+prefix+setParams(obj)
    this.onupdate.emit(obj)
  }

  update_value(p:any,$event: any) {
    p.value=$event;
    this.save_local()
  }

  open_test(mode='web') {
    this.create_url();
    let url=this.url;
    if(mode=="local"){
      url=this.url.split("//")[1]
      if(url.indexOf("/")>-1)url=url.substring(url.indexOf('/'))
      url="http://localhost:4200"+(url.startsWith("/") ? "" : "/")+url
    }
    open(url,"test")
  }


  share_url() {
    this.create_url();
    let obj:any={}
    for(let p of this.properties){
      obj[p.name]=p.value
    }
    this.ngShare.share({
      title:obj["appname"],
      url:obj["url"],
      text:obj["claim"]
    })
  }

  search_image() {
    open_image_banks(this)
  }
}
