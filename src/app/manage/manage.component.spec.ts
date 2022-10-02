import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ManageComponent } from './manage.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {RouterTestingModule} from "@angular/router/testing";
import {MatDialogModule} from "@angular/material/dialog";
import {AliasPipe} from "../alias.pipe";
import {FilterPipe} from "../filter.pipe";

describe('ManageComponent', () => {
  let component: ManageComponent;
  let fixture: ComponentFixture<ManageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ ManageComponent ,AliasPipe,FilterPipe],
      imports: [HttpClientModule,MatSnackBarModule,RouterTestingModule,MatDialogModule],
      providers:[
        {provide:AliasPipe,useValue:[]},
        {provide: FilterPipe,useValue: []}]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ManageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
