import {Component, Input, OnInit} from '@angular/core';

@Component({
  selector: 'app-link',
  templateUrl: './link.component.html',
  styleUrls: ['./link.component.css']
})
export class LinkComponent implements OnInit {

  @Input() content="";
  @Input() icon="";
  @Input() network="elrond-devnet";
  @Input() suffix=""
  @Input() title=""
  constructor() { }

  ngOnInit(): void {
    if(this.title=="")this.title="Explorer "+this.content
  }

  get_explorer(content: string,suffix="") {
    return "https://"+(this.network.indexOf('devnet')>-1 ? "devnet-" : "")+"explorer.elrond.com/address/"+content+suffix;
  }
}
