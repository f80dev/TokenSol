import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MatSnackBar} from "@angular/material/snack-bar";
import {showMessage} from "../../tools";

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
  @Input("send_file") send_file:boolean=false;
  @Input("encode") encode=true;
  @Input("maxsize") maxsize:number=10000000000000;
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
    for(let file of fileInputEvent.target.files){
      file.reader = new FileReader();
      if (file.size < this.maxsize) {
        this.filename = file.name;
        file.reader.onload = () => {
          let content = file.reader.result;
          this.message = "";
          if(!this.encode)content=atob(content);
          this.onupload.emit({
            filename:this.filename,
            file:content,
            type:content.split("data:")[1].split(";")[0]
          })
        }

        if(this.send_file){
          this.onupload.emit({filename:file.name,file:file})
        } else {
          this.message = "Chargement du fichier";
          file.reader.readAsDataURL(file);
        }

      } else {
        showMessage(this, "La taille limite des fichier est de " + Math.round(this.maxsize / 1024) + " ko");
        this.message = "";
        this.oncancel.emit();
      }
    }
  }
}
