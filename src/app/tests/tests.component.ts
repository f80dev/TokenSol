import {AfterViewInit, Component, OnInit} from '@angular/core';

@Component({
  selector: 'app-tests',
  templateUrl: './tests.component.html',
  styleUrls: ['./tests.component.css']
})
export class TestsComponent {

  num: boolean =true;
  objs: any[]=[{label:"label1",value:"value1"},{label:"label2",value:"value2"},{label:"label3",value:"value3"}]
  //objs=["value1","value2","value3"]
  obj:any=this.objs[0]


  constructor() {

  }



  ngOnInit(): void {
    //setTimeout(()=>{this.sel_option=this.opts[0];});
  }


  force() {
    this.obj={value:"label2",label:"value2"}
  }
}

