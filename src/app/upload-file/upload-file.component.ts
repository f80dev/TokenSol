import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MatSnackBar} from "@angular/material/snack-bar";
import {showMessage} from "../../tools";
import {MAX_FILE_SIZE} from "../../definitions";

@Component({
  selector: 'app-upload-file',
  templateUrl: './upload-file.component.html',
  styleUrls: ['./upload-file.component.css']
})
export class UploadFileComponent implements OnInit {

  message:string="";
  filename:string="";
  @Input("filter") filter:any={};
  @Input("title") title:string="";
  @Input("icon") icon:string="";
  @Input("send_file") send_file:boolean=false;
  @Input() width:string="fit-content";
  @Input("encode") encode=true;
  @Input() format="binary";
  @Input() can_drop:boolean=true;
  @Input("maxsize") maxsize:number=MAX_FILE_SIZE;
  @Input("show_cancel") show_cancel:boolean=false;
  @Output("uploaded") onupload:EventEmitter<any>=new EventEmitter();
  @Output("canceled") oncancel:EventEmitter<any>=new EventEmitter();
  @Input("extensions") extensions:string="*"; //format: accept=".doc,.docx"  ou "accept="audio/*"



  constructor(
    public toast:MatSnackBar,
  ) { }

  ngOnInit(): void {
  }

  cancel(){
    this.oncancel.emit();
  }

  import(fileInputEvent: any) {
    let files=fileInputEvent.hasOwnProperty("isTrusted") ? fileInputEvent.target.files : fileInputEvent;
    for(let file of files){
      file.reader = new FileReader();
      if (file.size < this.maxsize) {
        this.filename = file.name;
        file.reader.onload = () => {
          let content = file.reader.result;
          this.message = "";
          if(!this.encode)content=atob(content);
          if(this.format=="text"){
            this.onupload.emit({
              filename:file.name,
              file:content,
              type:"plain/txt"
            })
          }else{
            this.onupload.emit({
              filename:file.name,
              file:content,
              type:content.split("data:")[1].split(";")[0]
            })
          }

        }

        if(this.send_file){
          this.onupload.emit({filename:file.name,file:file})
        } else {
          this.message = "Chargement du fichier";
          if(this.format=="binary")
            file.reader.readAsDataURL(file);
          else
            file.reader.readAsText(file,"utf-8")
        }

      } else {
        showMessage(this, "La taille limite des fichier est de " + Math.round((this.maxsize / 1024)/1024) + " Mo",10000);
        this.message = "";
        this.oncancel.emit();
      }
    }
  }
}
