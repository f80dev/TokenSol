import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {Operation} from "../../operation";
import {showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {environment} from "../../environments/environment";
import {Validator} from "../../nft";


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
      this.refresh();
    })
  }

  refresh(){
    this.network.get_validators().subscribe((validators:Validator[])=>{
      this.validators=[];
      for(let validator of validators){
        validator.qrcode_accesscode=environment.server + "/api/qrcode/" + encodeURIComponent(validator.access_code);
        validator.dtStart=Math.round((new Date().getTime()-1000*(Number(validator.dtStart)))/(60*1000))
        this.validators.push(validator);
      }
    })
  }


  desactivate() {
  }


  update_operation(validator:Validator) {
      this.network.set_operation_for_validator(validator.id,validator.ask).subscribe(()=>{
        showMessage(this,"Validateur à jour");
        this.refresh();
      })
  }

  delete(validator: Validator) {
    this.network.remove_validator(validator.id).subscribe(()=>{
      this.refresh();
    })
  }


  delete_all() {
    let i=0;
    for(let val of this.validators)
      this.network.remove_validator(val.id).subscribe(()=>{
        i++;
        if(i==this.validators.length){
          this.refresh();
          showMessage(this,"Validateurs supprimés");
        }

      })
  }
}
