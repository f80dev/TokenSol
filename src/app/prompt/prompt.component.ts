import {Component, Inject, OnInit} from '@angular/core';
import {MAT_DIALOG_DATA, MatDialogRef} from "@angular/material/dialog";

export function _prompt(vm:any,title:string,_default:string="",description="",_type="text",lbl_ok="ok",lbl_cancel="Annuler",onlyConfirm=false,options:any=null):Promise<string> {
  return new Promise((resolve, reject) => {
    if(_type=="yesorno" || _type=="boolean" || _type=="bool")onlyConfirm=true;
    vm.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: title,
          type: _type,
          question:description,
          options:options,
          result:_default,
          onlyConfirm:onlyConfirm,
          lbl_ok:lbl_ok,
          lbl_cancel:lbl_cancel
        }
    }).afterClosed().subscribe((resp:any) => {
      if(resp) {
        resolve(resp);
      } else {
        reject()
      }
    },(err:any)=>{reject(err)});
  });
}



export interface DialogData {
  title: string;
  result: any;
  question:string;
  placeholder:string;
  onlyConfirm:boolean;
  min:number,
  image:string,
  n_rows:number,
  max:number,
  emojis:boolean;
  lbl_ok:string,
  type:string,
  lbl_cancel:string,
  lbl_sup:string,
  options:any[],
  subtitle:string
}


@Component({
  selector: 'app-prompt',
  templateUrl: './prompt.component.html',
  styleUrls: ['./prompt.component.css']
})

export class PromptComponent  {

  showEmoji=false;
  _type="text";
  // @ts-ignore
  _min!: number;
  // @ts-ignore
  _max!: number;

  constructor(
    public dialogRef_prompt: MatDialogRef<PromptComponent>,
    @Inject(MAT_DIALOG_DATA) public data: DialogData)
  {
    if(this._type=="oui/non")data.onlyConfirm=true;
    if(this._type=="images")data.result=[];
    if(data.onlyConfirm)data.result="yes";
    if(data.min){
      this._min=data.min;
      this._type="number";
    }
    if(data.max){
      this._max=data.max;
      this._type="number";
    }
    if(data.hasOwnProperty("type"))this._type=data.type;
    if(!data.result)data.result="";
    if(!data.n_rows)data.n_rows=4;
    if(this._type=="string" || this._type=="str")this._type="text";
  }

  onNoClick(): void {
    this.dialogRef_prompt.close(null);
  }

  selectEmoji(event:any){
    this.data.result=this.data.result+event.emoji.native;
    this.showEmoji=false;
  }


  onEnter(evt:any) {
    if(evt.keyCode==13)
      this.dialogRef_prompt.close(this.data.result);
  }

  select_option(value: any) {
    this.dialogRef_prompt.close(value);
  }


  select_image(img:any) {
    if(this.data.result=="")this.data.result=[];
    let index=this.data.result.indexOf(img);
    if(index>-1){
      this.data.result.splice(index,1);
    } else {
      this.data.result.push(img);
    }
  }

    select_all() {
      this.dialogRef_prompt.close(this.data.options)
    }
}
