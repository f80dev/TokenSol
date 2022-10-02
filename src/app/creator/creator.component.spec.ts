import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreatorComponent } from './creator.component';
import {HttpClientModule} from "@angular/common/http";
import {RouterTestingModule} from "@angular/router/testing";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import {MatDialogModule} from "@angular/material/dialog";
import {AliasPipe} from "../alias.pipe";
import {SafePipe} from "../safe.pipe";
import {ClipboardModule} from "@angular/cdk/clipboard";

describe('CreatorComponent', () => {
  let component: CreatorComponent;
  let fixture: ComponentFixture<CreatorComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ CreatorComponent ],
      imports: [HttpClientModule,RouterTestingModule,MatSnackBarModule,MatDialogModule,ClipboardModule],
      providers: [{provide:SafePipe}]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CreatorComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
