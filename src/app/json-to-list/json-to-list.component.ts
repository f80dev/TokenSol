import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';

@Component({
  selector: 'app-json-to-list',
  templateUrl: './json-to-list.component.html',
  styleUrls: ['./json-to-list.component.css']
})
export class JsonToListComponent implements OnInit,OnChanges {

  @Input() data:any
  keys:string[]=[];

  constructor() { }

  ngOnInit(): void {

  }

  ngOnChanges(changes: SimpleChanges): void {
    if(this.data){
      if(typeof(this.data)=="string")this.data=JSON.parse(this.data);
      this.keys=Object.keys(this.data);
    }
  }

}
