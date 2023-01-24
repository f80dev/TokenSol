import {Component, Input, OnDestroy, OnInit} from '@angular/core';

@Component({
  selector: 'app-warning',
  templateUrl: './warning.component.html',
  styleUrls: ['./warning.component.css']
})
export class WarningComponent implements OnInit,OnDestroy {
  @Input("if") _if: boolean=false;
  handle:any;
  visibility: boolean=true;
  @Input() help: string="";

  ngOnInit(): void {
    this.handle=setInterval(()=>{this.visibility=!this.visibility},200);
  }

  ngOnDestroy(): void {
    clearInterval(this.handle);
  }

}
