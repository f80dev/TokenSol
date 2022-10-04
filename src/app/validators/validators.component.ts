import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {Operation} from "../../operation";
import {setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {environment} from "../../environments/environment";

export interface Validator {
  id:string
  name: string | ""
  operation: string | ""
  user: string | ""
  dtLastConnexion: number | 0
  dtStart: Number | 0
  nfts: Number | 0
  qrcode_accesscode: string | ""
  access_code:string | ""
}

@Component({
  selector: 'app-validators',
  templateUrl: './validators.component.html',
  styleUrls: ['./validators.component.css']
})
export class ValidatorsComponent implements OnInit {
  validators: Validator[]=[];
  operations: Operation[]=[];

  constructor(
    public network:NetworkService,
    public toast:MatSnackBar
  ) { }


  ngOnInit(): void {
    this.network.get_operations().subscribe((operations:any)=>{
      this.operations=operations;
      this.network.get_validators().subscribe((validators:Validator[])=>{
        this.validators=[];
        for(let validator of validators){
          validator.qrcode_accesscode=environment.server + "/api/qrcode/" + encodeURIComponent(validator.access_code);
          this.validators.push(validator);
        }
      })
    })
  }


  desactivate() {
  }


  update_operation(validator:Validator) {
      this.network.set_operation_for_validator(validator.id,validator.operation).subscribe(()=>{
        showMessage(this,"Validateur à jour");
      })
  }
}
