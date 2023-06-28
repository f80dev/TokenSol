import {AfterViewInit, Component, OnInit} from '@angular/core';

@Component({
  selector: 'app-tests',
  templateUrl: './tests.component.html',
  styleUrls: ['./tests.component.css']
})
export class TestsComponent {

  num: boolean =true;

  constructor() {

  }



  ngOnInit(): void {
    //setTimeout(()=>{this.sel_option=this.opts[0];});
  }


}

