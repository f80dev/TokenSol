import {AfterViewInit, Component, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-tests',
  templateUrl: './tests.component.html',
  styleUrls: ['./tests.component.css']
})
export class TestsComponent {

  num: any;
  nums: any[]=[];
  objs: any[]=[{label:"label1",value:"value1"},{label:"label2",value:"value2"},{label:"label3",value:"value3"}]
  //objs=["value1","value2","value3"]
  obj:any=this.objs[0]


  constructor(public api:NetworkService) {

  }



  ngOnInit(): void {

    setTimeout(async  ()=>{
      let keys=await this.api.init_keys(false,"","","elrond-devnet")
      this.nums=[{label:keys[0].name,value:keys[0]},{label:keys[1].name,value:keys[1]}]
    },3000);
  }


  force() {
    this.obj={value:"label2",label:"value2"}
  }
}

