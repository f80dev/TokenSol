import {AfterViewInit, Component, ElementRef, Input, OnChanges, OnInit, SimpleChanges, ViewChild} from '@angular/core';
import * as d3 from "d3";
import {Location} from "@angular/common";
import {ActivatedRoute, Router} from "@angular/router";
import {$$, showError} from "../../tools";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-visgraph',
  templateUrl: './visgraph.component.html',
  styleUrls: ['./visgraph.component.sass']
})
export class VisgraphComponent implements OnChanges {
  private svg: any;

  simulation: any;
  forceProperties = {
    center: {
      x: 1,
      y: 0.5
    },
    charge: {
      enabled: true,
      strength: -500,
      distanceMin: 1,
      distanceMax: 300
    },
    collide: {
      enabled: true,
      strength: .7,
      iterations: 1,
      radius: 5
    },
    forceX: {
      enabled: false,
      strength: .1,
      x: .5
    },
    forceY: {
      enabled: false,
      strength: .1,
      y: .5
    },
    link: {
      enabled: true,
      distance: 30,
      iterations: 1
    }
  };

  name: string = "";
  @Input() data: any;
  sel_node: any = null;

  props = ["pagerank", "centrality"]
  filter: any = {
    pagerank: {value: 0.0005, min: 1000, max: -1000, step: 0},
    centrality: {value: 0.0005, min: 1000, max: -1000, step: 0}
  };
  selFilter = this.props[0];

  message: string = "";
  edge_props: any;
  width = screen.availWidth;
  height = screen.availHeight;

  @ViewChild('graph_zone') graph_zone: ElementRef | null = null;

  constructor(
    public api: NetworkService,
    public router: Router,
    public _location: Location,
    public routes: ActivatedRoute,
  ) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if(!this.svg){
      this.svg=this.createSvg(this.width,this.height,-this.height/4);
      this.initializeForces(this.data,this.svg);
    }
    this.resetGraph(this.svg);
    this.refresh();
  }



  createSvg(width:number,height:number,margin:number): any {
    return d3.select("figure#graph")
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .append("g")
      .attr("transform", "translate(" + (-width/4) + "," + (-height/8) + ")");
  }

  resetGraph(svg:any){
    svg.selectAll("g").remove();
    svg.selectAll("line").remove();
    svg.selectAll("circle").remove();
  }


  initializeForces(data:any,svg:any) {
    if(!data || !data.edges || !data.nodes)return;
    $$("Données traitées ",data);
    var link = svg
      .selectAll("line")
      .data(data.edges)
      .enter()
      .append("line")
      .property("edgeid",(d:any) => {return d.id;})
      .property("name",(d:any)=>{return d.title;})
       .on("mouseenter", (d:any)=>{this.mouseenter(d);})
      .on("mouseleave", (d:any)=>{this.mouseleave(d);})
      .style("stroke", "#aaa")

    var nodeEnter = svg
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("svg:g")
      .attr("class", "node")
      .property("name",function(d:any) { return d.label;})
      .property("id", function(d:any) { return d.id;})
      .on("mouseenter", (d:any)=>{this.mouseenter(d);})
      .on("mouseleave", (d:any)=>{this.mouseleave(d);})
      .on("click", (d:any)=>{this.click(d);})
      .on("dblclick", (d:any)=>{this.sel(d);});

    var node = nodeEnter.append("svg:image")
      .attr("xlink:href",  function(d:any) { return d.photo;})
      .attr("title",function (d:any) {return d.firstname+" "+d.lastname;})
      .attr("x", function(d:any) { return -25;})
      .attr("y", function(d:any) { return -25;})
      .attr("height", 50)
      .attr("width", 50)

    nodeEnter.append("svg:text")
      .text(function(d:any) { return d.name;})

    // add forces and associate each with a name
    this.simulation=d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink().id((d:any) => { return d.id; }).links(data.edges))
      .force("charge", d3.forceManyBody())
      .force("collide", d3.forceCollide())
      .force("center", d3.forceCenter())
      .force("forceX", d3.forceX())
      .force("forceY", d3.forceY())
      .on("tick",()=>{
        link
          .attr("x1", function(d:any) { return d.source.x; })
          .attr("y1", function(d:any) { return d.source.y; })
          .attr("x2", function(d:any) { return d.target.x; })
          .attr("y2", function(d:any) { return d.target.y; });

        node
          .attr("x", function (d:any) { return d.x-25; })
          .attr("y", function(d:any) { return d.y-25; })
          .attr("opacity", (d:any)=> {
            let opacity=1;
            for(let p of this.props){
              if(d[p]<this.filter[p].value){
                opacity=0.1;
                break;
              }
            }
            return opacity;
          });

      });

    this.updateForces(this.width,this.height);
  }



  updateForces(width:number,height:number) {
    // get each force by name and update the properties
    this.simulation.force("center")
      .x(width * this.forceProperties.center.x)
      .y(height * this.forceProperties.center.y);
    this.simulation.force("charge")
      .strength(this.forceProperties.charge.strength * Number(this.forceProperties.charge.enabled))
      .distanceMin(this.forceProperties.charge.distanceMin)
      .distanceMax(this.forceProperties.charge.distanceMax);
    this.simulation.force("collide")
      .strength(this.forceProperties.collide.strength * Number(this.forceProperties.collide.enabled))
      .radius(this.forceProperties.collide.radius)
      .iterations(this.forceProperties.collide.iterations);
    this.simulation.force("forceX")
      .strength(this.forceProperties.forceX.strength * Number(this.forceProperties.forceX.enabled))
      .x(width * this.forceProperties.forceX.x);
    this.simulation.force("forceY")
      .strength(this.forceProperties.forceY.strength * Number(this.forceProperties.forceY.enabled))
      .y(height * this.forceProperties.forceY.y);
    this.simulation.force("link")
      .id(function(d:any) {return d.id;})
      .distance(this.forceProperties.link.distance)
      .iterations(this.forceProperties.link.iterations)
      .links(this.forceProperties.link.enabled ? this.data.edges : []);

    // updates ignored until this is run
    // restarts the simulation (important if simulation has already slowed down)
    this.simulation.alpha(1).restart();
  }



  mouseenter(d:any){
    let data=d.target.__data__;
    if(data.hasOwnProperty("source")){
      this.sel_node={label:"<strong>"+data.data.title+"</strong> "+data.data.year};
    }else{
      this.sel_node={label:"<strong>"+data.label +"</strong><br>"+data.formation+" "+data.promo};
    }

  }

  mouseleave(d:any){
    this.sel_node=null;
  }

  click(d:any){
    // this.forceProperties.center.x=d.x/this.width;
    // this.forceProperties.center.y=d.y/this.height;
    // this.updateForces();
  }


  sel_edge(d:any){
    let prop=this.edge_props[d.target.__data__.index];
  }




  //Sélection d'un noeud

  sel(d: any) {
    this.router.navigate(["search"],{queryParams:{filter:d.target.__data__.lastname}})
  }


  update_filter(data:any) {
    //Détermine le max et le min des filtre
    if(this.filter){
      for(let n of data.nodes){
        for(let k of this.props) {
          if(n[k]<this.filter[k].min)this.filter[k].min=n[k];
          if(n[k]>this.filter[k].max)this.filter[k].max=n[k];
        }
      }

      //Positionne les filtres sur la plus basse valeure
      for(let k of this.props){
        this.filter[k].value=this.filter[k].min;
        this.filter[k].step=(this.filter[k].max-this.filter[k].min)/100;
      }
    }

  }



  refresh() {
    this.edge_props=this.data.edge_props;
    this.update_filter(this.data);
    this.initializeForces(this.data,this.svg);
  }

  ngAfterViewInit(): void {
    if(this.graph_zone){
      this.width=this.graph_zone.nativeElement.clientWidth;
      this.height=this.graph_zone.nativeElement.clientHeight;
    }
    this.refresh();
  }

  clear_filter() {
    this.filter.department.value="";
    this.filter.promo.value=null;
    this.refresh()
  }
}

