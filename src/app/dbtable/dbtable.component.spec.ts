import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DbtableComponent } from './dbtable.component';
import {HttpClientModule} from "@angular/common/http";
import {MatSnackBarModule} from "@angular/material/snack-bar";

describe('DbtableComponent', () => {
  let component: DbtableComponent;
  let fixture: ComponentFixture<DbtableComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ DbtableComponent ],
      imports: [HttpClientModule,MatSnackBarModule]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DbtableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
