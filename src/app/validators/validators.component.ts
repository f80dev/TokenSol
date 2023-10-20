import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import { Operation} from "../../operation";
import {$$, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Validator} from "../../nft";
import {Router} from "@angular/router";
import {MatDialog} from "@angular/material/dialog";
import {OperationService} from "../operation.service";
import {Socket} from "ngx-socket-io";

@Component({
  selector: 'app-validators',
  templateUrl: './validators.component.html',
  styleUrls: ['./validators.component.css']
})
export class ValidatorsComponent implements OnInit {
  validators: Validator[]=[];
  operations: Operation[]=[];
  deleting_all: boolean=false;

  constructor(
      public network:NetworkService,
      public operation:OperationService,
      public toast:MatSnackBar,
      public router:Router,
      public dialog:MatDialog,
      public socket:Socket
  ) { }


  ngOnInit(): void {
    this.network.get_operations().subscribe((operations:any)=>{
      this.operations=operations;
      this.refresh();
    })
    this.socket.on("refresh",()=>{
      if(!this.deleting_all)this.refresh();
    })
    // this.socket.fromEvent("refresh").pipe(map((data:any)=>{
    //   $$("Réception du message de refresh");
    //   this.refresh();
    // }));
  }

  refresh(){
    $$("Refresh des validateurs");
    this.network.get_validators().subscribe((validators:Validator[])=>{
      this.validators=[];
      for(let validator of validators){
        validator.qrcode_accesscode=this.network.server_nfluent + "/api/qrcode/" + encodeURIComponent(validator.access_code);
        validator.delayFromStart=Math.round((new Date().getTime()-1000*(Number(validator.dtStart)))/(60*1000))
        this.validators.push(validator);
      }
    })
  }


  desactivate(validator:Validator) {
    this.network.send_message_to_validator(validator.id,"stop").subscribe(()=>{
      showMessage(this,"Message envoyé");
    })
  }


  update_operation(validator:Validator) {
    this.network.set_operation_for_validator(validator.id,validator.ask).subscribe(()=>{
      showMessage(this,"Validateur à jour");
      this.refresh();
    })
  }

  delete(validator: Validator) {
    this.network.remove_validator(validator.id).subscribe(()=>{this.refresh();})
  }


  delete_all() {
    let i=0;
    this.deleting_all=true;
    this.network.wait("Validateurs en cours de suppression")
    for(let val of this.validators){
      setTimeout(()=>{this.network.remove_validator(val.id).subscribe(()=>{})},500*i);
      i++;
    }
    setTimeout(()=>{
      this.refresh();
      this.deleting_all=false;
      this.network.wait();
      showMessage(this,"Validateurs supprimés");
    },i*500)

  }

  receive_nft(validator:any) {
    this.network.get_nfts_from_collection(validator.ask,this.network.network).subscribe((result)=>{
      let nft=result.nfts[0];
      let param=setParams({
        token:nft,
        section:"store"
      },"","")
      this.router.navigate(["dm"],{queryParams:{p:param}});
    })

  }
}
