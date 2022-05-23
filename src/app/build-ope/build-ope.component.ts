import { Component, OnInit } from '@angular/core';
import {MatSelectChange} from "@angular/material/select";
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";
import {showMessage} from "../../tools";

@Component({
  selector: 'app-build-ope',
  templateUrl: './build-ope.component.html',
  styleUrls: ['./build-ope.component.css']
})
export class BuildOpeComponent implements OnInit {
  selected_ope: any={};
  url: string = "";
  opes: any[]=[];
  iframe_code: string="";
  image_code: string="";

  constructor(
    public network:NetworkService,
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    this.network.get_operations().subscribe((r:any)=>{
      this.opes=r;
      if(this.selected_ope=="")this.selected_ope=r[0];
    })
  }

  refresh_ope($event: MatSelectChange) {
    let ope=$event.value.code.replace(".yaml","");
    this.url=environment.appli+"/contest?ope="+ope;
    this.iframe_code="<iframe src='"+this.url+"&mode=iframe'></iframe>";
    this.image_code="<img src='"+environment.server+"/api/get_new_code/"+ope+"/?format=qrcode'>";
  }

  upload_operation($event: any) {
    this.network.upload_operation($event.filename,$event.file).subscribe((r:any)=>{
      showMessage(this,"Opération importée");
      this.refresh();
    })
  }

  new_model() {
    open(environment.appli+"/assets/new_operation.yaml","blank","");
  }

  delete_ope() {
    this.network.delete_operation(this.selected_ope.code).subscribe(()=>{
      this.refresh();
    });
  }
}
